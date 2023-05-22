# CNStockGPT
基于GPT的人工智能炒股程序

### 说明
1. 用同花顺问财AI进行技术面筛选
2. 使用akshare查询网上最新资料
3. ChatGPT进行分析并打分

### 如何运行
1. pip install -r requirements.txt
2. 访问https://chat.openai.com/api/auth/session ,获取access_token,然后新建.env文件，写入CHATGPT="获取的token"
3. 运行main.py,将会生成html文件

### TODO
自动调仓雪球组合，可以一键跟单

