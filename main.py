import ast
import os
import re
from copy import deepcopy

import numpy as np
import pandas as pd
import requests
from datetime import *
import time as t
from dotenv import load_dotenv
from revChatGPT.V1 import Chatbot as ChatGPT
import akshare as ak


PROXY='http://127.0.0.1:7890'
load_dotenv(dotenv_path= '.env')
# print("CHATGPT=====",CHATGPT)
def hot(timeType='day',listType='normal'):
    '''
    timeType:day,hour
    listType:normal,skyrocket,tech,value,trend
    '''
    params = {
        'stock_type': 'a',
        'type': timeType,
        'list_type': listType,
    }
    response = requests.get(
        'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock',
        params=params,
        headers={'User-Agent': 'Mozilla'},
    )
    stock_list=response.json()['data']['stock_list'];
    stock_list=stock_list[0:1]
    return pd.DataFrame(stock_list)


def renderHtml(df,filename:str,title:str):
    df.index = np.arange(1, len(df) + 1)
    df.index.name='No.'
    df.reset_index(inplace=True)
    #pd.set_option('colheader_justify', 'center')
    html_string = '<html><head><title>%s</title>{style}</head><body>{table}{tablesort}</body></html>'%title
    html_string = html_string.format(
        table=df.to_html(render_links=True, escape=False, index=False),
        style='<link rel="stylesheet" type="text/css" href="static/table.css"/>',
        tablesort='<script src="static/tablesort.min.js"></script><script src="static/tablesort.number.min.js"></script><script>new Tablesort(document.getElementById("container"));</script>',
    )
    with open(filename, 'w') as f:
        f.write(html_string.replace('<table border="1" class="dataframe">','<table id="container">').replace('<th>','<th role="columnheader">'))

class Bot():
    def __init__(self):
        self.chatgptBot = None
    def chatgpt(self, queryText: str):
        reply_text,convId = None,None
        if self.chatgptBot is None:
            self.chatgptBot =ChatGPT(config={"access_token": os.environ['CHATGPT'],'proxy':PROXY})
        
        print("queryText====",queryText)
        for data in self.chatgptBot.ask(queryText):
            convId=data['conversation_id']
            reply_text = data["message"]
            print(convId,reply_text)
        try:
            t.sleep(2)
            self.chatgptBot.delete_conversation(convId)
        except:
            pass
        return reply_text


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 去同花顺取100条最热股票
    wdf = hot()
    # 写到本地
    wdf.to_csv('wencai_o.csv',index=False)
    # print(list(wdf.iterrows()))
    # exit()
    wdf.set_index('code',inplace=True)
    bot=Bot()
    # print(list(wdf.iterrows()))
    # exit()
    for k,v in wdf.iterrows():
        # 通过market从前面的字典里找到对应的市场，再把代码拼在后面
        symbol={17:'SH',33:'SZ'}[v['market']]+k
        # 找到代码对应的stock字段，把雪球链接拼接进去
        wdf.at[k,'stock']='<a href="https://xueqiu.com/S/%s">%s<br>%s</a>'%(symbol,symbol,v['name'])

        # 去东财根据股票代码拉去最新的100条新闻
        news=ak.stock_news_em(k)

        # 删除重复标题的新闻内容
        news.drop_duplicates(subset='新闻标题',inplace=True)

        # 这一行是将 news 中的 ‘发布时间’ 这一列转换成 datetime 类型，方便后续的处理。
        news['发布时间']=pd.to_datetime(news['发布时间'])

        # 这一行是将 news 中的 ‘新闻标题’ 这一列进行修改，首先在标题前面加上发布时间的年月日，然后去掉标题中包含 v[‘name’] 的部分，v[‘name’] 是一个变量，可能是一个股票名称或者其他内容。
        news['新闻标题']=news['发布时间'].dt.strftime('%Y-%m-%d ')+news['新闻标题'].str.replace('%s：'%v['name'],'')
        
        # 这一行是将 news 中的 ‘新闻标题’ 这一列进行筛选，只保留不包含 ‘股’、‘主力’、‘机构’ 或者 ‘资金流’ 这些词的新闻，用 ~ 表示取反，用 | 表示或者。
        news = news[~news['新闻标题'].str.contains('股|主力|机构|资金流')]

        # 这一行是将 news 中的 ‘新闻标题’ 和 ‘新闻内容’ 这两列进行拼接，形成一个新的列 ‘news’。首先将 ‘新闻内容’ 这一列按照句号分割，然后取第一个句子，也就是新闻的摘要。然后将 ‘新闻标题’ 和新闻摘要用空格连接起来，形成一个完整的新闻信息。
        news['news']=news['新闻标题'].str.cat(news['新闻内容'].str.split('。').str[0], sep=' ')

        # 这一列进行筛选，只保留包含 v[‘name’] 的新闻，v[‘name’] 是一个变量，可能是一个股票名称或者其他内容。
        news = news[news['news'].str.contains(v['name'])]

        # 这一行是将 news 按照 ‘发布时间’ 这一列进行排序，按照降序排列，即最新的新闻在最前面。inplace=True 表示在原地修改 news 对象，而不是返回一个新的对象。
        news.sort_values(by=['发布时间'],ascending=False,inplace=True)
        # news=news[news['发布时间']> datetime.now() - timedelta(days=30)]



        if len(news)<2:
            continue

        # 它的功能是从一个名为news的数据框中提取前30条新闻标题，并用换行符连接成一个字符串，然后截取前1800个字符。这样就可以得到一个包含30条新闻标题的简短文本。
        newsTitles='\n'.join(news['新闻标题'][:30])[:1800]

        # 这段代码也是用Python语言编写的，它的功能是根据一个变量v的name属性和之前生成的新闻标题文本，创建一个名为prompt的字典，其中包含一个键值对，键是v的name属性加上“相关资讯”，值是新闻标题文本。然后它要求用户分析总结机会点和风险点，并输出一个格式为{'机会':'''1..\n2..\n...''',\n'风险':'''1..\n2..\n...''',\n'题材标签':[标签]}的字典。
        prompt="{'%s相关资讯':'''%s''',\n}\n请分析总结机会点和风险点，输出格式为{'机会':'''1..\n2..\n...''',\n'风险':'''1..\n2..\n...''',\n'题材标签':[标签]}"%(v['name'],newsTitles)

        print('Prompt:\n%s'%prompt)


        # 这段代码也是用Python语言编写的，它的功能是调用一个名为bot的对象的chatgpt方法，传入之前创建的prompt字典作为参数，然后打印出返回的文本，
        # 命名为replyTxt。然后它用正则表达式从replyTxt中提取出最后一个花括号内的内容，命名为content，并用ast模块将其转换为一个Python字典，命名为parsed。
        # 然后它根据parsed字典中的“机会”和“风险”键的值的类型，分别将其转换为一个字符串，命名为chances和risks，并去掉其中包含v的name属性的部分。
        # 然后它用wdf这个数据框的at方法，将chances和risks赋值给第k行的“chance”和“risk”列，并用换行符替换掉其中的<br>标签。
        # 然后它根据risks是否包含换行符，计算出chances和risks的长度差，并赋值给第k行的“score”列。
        # 最后，它将parsed字典中的“题材标签”键的值转换为一个字符串，并用<br>标签连接起来，并赋值给第k行的“tags”列。
        retry=2
        while retry>0:
            try:
                print("开始调用GPT")
                replyTxt = bot.chatgpt(prompt)
                print('ChatGPT:\n%s'%replyTxt)
                # 它的功能是用re模块的findall方法，从replyTxt这个字符串中找出所有匹配正则表达式r’{[{}]*}‘的子字符串，并返回一个列表，赋值给match这个变量。
                # 正则表达式r’{[{}]*}'的意思是匹配以左花括号开始，以右花括号结束，中间不包含任何花括号的字符串。
                match = re.findall(r'{[^{}]*}', replyTxt)

                # 它的功能是从match这个列表中取出最后一个元素，赋值给content这个变量。match[-1]的意思是取出列表中索引为-1的元素，-1表示倒数第一个
                content = match[-1]
               

                # 这是一行Python代码，它的功能是用ast模块的literal_eval函数，将content这个字符串转换为一个Python对象，赋值给parsed这个变量。
                # ast模块是用来处理抽象语法树的模块，literal_eval函数是用来安全地评估一个字面量表达式的函数，比如一个数字，一个字符串，一个列表，一个字典等。
                parsed = ast.literal_eval(content)

                # 这是一个Python表达式，它的功能是判断parsed字典中的“机会”键的值是否是一个列表类型。
                if isinstance(parsed['机会'], list):
                    # 它的功能是用’\n’这个字符串作为分隔符，将一个生成器表达式生成的字符串序列连接起来，赋值给chances这个变量。生成器表达式的功能是遍历parsed字典中的“机会”键的值（一个列表），并对每个元素进行格式化，加上序号和点号，形成一个新的字符串。
                    # 这样就可以得到一个包含parsed字典中的“机会”键的值的所有元素，并用换行符分隔的字符串。
                    chances = '\n'.join( '%s. %s'%(x+1,parsed['机会'][x]) for x in range(len(parsed['机会'])))
                else:
                    chances = parsed['机会']
                if isinstance(parsed['风险'], list):
                    risks = '\n'.join('%s. %s'%(x+1,parsed['风险'][x]) for x in range(len(parsed['风险'])))
                else:
                    risks = parsed['风险']

                # 它的功能是用wdf这个数据框的at方法，将chances这个字符串去掉其中包含v的name属性的部分，并用<br>标签替换掉其中的换行符，然后赋值给第k行的“chance”列。
                # wdf是一个数据框，类似于一个表格，at方法是用来访问或修改某一行某一列的值的方法，k是一个变量，表示行索引，“chance”是一个字符串，表示列名。
                # chances是一个字符串，replace方法是用来替换字符串中的子字符串的方法。
                wdf.at[k, 'chance'] = chances.replace(v['name'], '').replace('\n', '<br>')
                wdf.at[k, 'risk'] = risks.replace(v['name'], '').replace('\n', '<br>')

                # print("score=",(len(chances) - len(risks)))

                if '\n' in risks:
                    wdf.at[k, 'score'] = len(chances) - len(risks)
                wdf.at[k,'tags'] = '<br>'.join(parsed['题材标签'])
                break
            except Exception as e:
                print(e)
                retry-=1
                prompt+='，请务必保持python dict格式'
                t.sleep(20)
                continue
        t.sleep(20)

    # 这一行的作用是删除wdf中score列中有缺失值的行1 。subset参数指定要检查缺失值的列，inplace参数指定是否在原对象上修改
    wdf.dropna(subset=['score'],inplace=True)

    # 这一行的作用是按照wdf中score列的值降序排序wdf。by参数指定要排序的列，ascending参数指定是否升序，inplace参数同上
    wdf.sort_values(by=['score'],ascending=False,inplace=True)
    wdf.to_csv('wencai.csv')

    # 这一行的作用是选择wdf中的某些列，并赋值给wdf。这样可以只保留需要的列，或者改变列的顺序。
    wdf=wdf[['stock','chance','risk','tags','score']]
    nowTxt=datetime.now().strftime('%Y-%m-%d')
    renderHtml(wdf,nowTxt+'.html',nowTxt)