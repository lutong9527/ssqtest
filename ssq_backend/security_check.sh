#!/bin/bash

echo "=========================================="
echo "       安全检测脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "===== 1. SECRET_KEY 检查 ====="
SECRET_LINE=$(grep SECRET_KEY .env 2>/dev/null)
if [ -z "$SECRET_LINE" ]; then
    echo -e "${RED}✗ 未找到 SECRET_KEY${NC}"
    echo "  改进: 在 .env 中添加 SECRET_KEY=your-random-secret-key"
elif echo "$SECRET_LINE" | grep -q "your-secret-key\|change-this\|example\|123456\|secret"; then
    echo -e "${RED}✗ SECRET_KEY 使用默认/弱值${NC}"
    echo "  当前值: $SECRET_LINE"
    echo "  改进: 使用强随机密钥，如:"
    echo "        openssl rand -hex 32"
    echo "        或 Python: import secrets; print(secrets.token_hex(32))"
else
    echo -e "${GREEN}✓ SECRET_KEY 已设置${NC}"
    echo "  当前值: ${SECRET_LINE:0:30}..."
fi

echo ""
echo "===== 2. 数据库密码检查 ====="
DB_URL=$(grep DATABASE_URL .env 2>/dev/null)
if [ -z "$DB_URL" ]; then
    echo -e "${RED}✗ 未找到 DATABASE_URL${NC}"
    echo "  改进: 添加 DATABASE_URL=mysql+pymysql://user:pass@host/db"
else
    # 提取密码部分
    PASS=$(echo "$DB_URL" | grep -oP '://[^:]+:\K[^@]+' || echo "无法解析")
    if [ "$PASS" = "无法解析" ] || [ -z "$PASS" ]; then
        echo -e "${YELLOW}⚠ 无法解析密码格式${NC}"
        echo "  当前: $DB_URL"
    elif [ ${#PASS} -lt 8 ]; then
        echo -e "${RED}✗ 数据库密码过短 (${#PASS} 位)${NC}"
        echo "  改进: 使用至少12位强密码，包含大小写+数字+符号"
        echo "        示例: MyP@ssw0rd!2024"
    elif echo "$PASS" | grep -qi "password\|123\|admin\|root"; then
        echo -e "${RED}✗ 数据库密码使用常见弱密码${NC}"
        echo "  改进: 避免使用 password、123456 等常见密码"
    else
        echo -e "${GREEN}✓ 数据库密码强度合格${NC}"
        echo "  密码长度: ${#PASS} 位"
    fi
fi

echo ""
echo "===== 3. .env 文件暴露检查 ====="
ENV_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/.env 2>/dev/null)
if [ "$ENV_STATUS" = "200" ]; then
    echo -e "${RED}✗ 严重: .env 文件可通过 HTTP 访问!${NC}"
    echo "  风险: 数据库密码、密钥等全部泄露"
    echo "  紧急改进:"
    echo "    1. 立即在 nginx/apache 中屏蔽 .env 访问"
    echo "    2. 添加 .env 到 .gitignore"
    echo "    3. 修改所有泄露的密码和密钥"
    echo "    4. nginx 配置示例:"
    echo "       location ~ /\\. { deny all; }"
elif [ "$ENV_STATUS" = "404" ] || [ "$ENV_STATUS" = "403" ]; then
    echo -e "${GREEN}✓ .env 文件已正确屏蔽${NC}"
    echo "  HTTP 状态码: $ENV_STATUS"
else
    echo -e "${YELLOW}⚠ 无法检测 (服务未运行或状态码: $ENV_STATUS)${NC}"
    echo "  建议: 手动访问 http://your-domain/.env 确认无法访问"
fi

echo ""
echo "===== 4. CORS 配置检查 ====="
CORS_CONFIG=$(grep -R "allow_origins" . 2>/dev/null | head -5)
if [ -z "$CORS_CONFIG" ]; then
    echo -e "${YELLOW}⚠ 未找到 CORS 配置${NC}"
    echo "  建议: 显式配置 CORS，避免默认允许所有来源"
    echo "  FastAPI 示例:"
    echo "    allow_origins=['https://yourdomain.com']"
else
    if echo "$CORS_CONFIG" | grep -q "\*"; then
        echo -e "${RED}✗ CORS 允许所有来源 (*)${NC}"
        echo "  风险: 任何网站都可调用你的 API"
        echo "  改进: 限制特定域名"
        echo "    当前: $CORS_CONFIG"
        echo "    建议改为: allow_origins=['https://yourdomain.com']"
    else
        echo -e "${GREEN}✓ CORS 已限制特定来源${NC}"
        echo "  配置: $CORS_CONFIG"
    fi
fi

echo ""
echo "===== 5. root 弱密码测试 ====="
mysql -u root -proot -e "exit" 2>/dev/null && \
    echo -e "${RED}✗ root 使用弱密码 'root'${NC}" && \
    echo "  改进: mysql_secure_installation 设置强密码" || \
    (mysql -u root -e "exit" 2>/dev/null && \
        echo -e "${RED}✗ root 无密码可直接登录${NC}" && \
        echo "  改进: 立即设置密码: ALTER USER 'root'@'localhost' IDENTIFIED BY '强密码';" || \
        echo -e "${GREEN}✓ root 密码安全${NC}")

echo ""
echo "===== 6. 额外安全检查 ====="

# 检查是否运行在非 root 用户
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${YELLOW}⚠ 当前以 root 运行脚本${NC}"
    echo "  建议: 应用服务使用普通用户运行"
else
    echo -e "${GREEN}✓ 当前非 root 用户${NC}"
fi

# 检查 .env 文件权限
if [ -f ".env" ]; then
    PERM=$(stat -c %a .env 2>/dev/null || stat -f %Lp .env 2>/dev/null)
    if [ "$PERM" -gt 644 ]; then
        echo -e "${YELLOW}⚠ .env 文件权限过于开放 ($PERM)${NC}"
        echo "  改进: chmod 600 .env"
    else
        echo -e "${GREEN}✓ .env 文件权限正确 ($PERM)${NC}"
    fi
else
    echo -e "${RED}✗ .env 文件不存在${NC}"
fi

echo ""
echo "=========================================="
echo "           检测完成"
echo "=========================================="
echo ""
echo "📋 改进优先级清单:"
echo "  [紧急] 修复标有 ✗ 的红色项目"
echo "  [建议] 处理标有 ⚠ 的黄色项目"
echo "  [良好] 保持标有 ✓ 的绿色项目"
echo ""
