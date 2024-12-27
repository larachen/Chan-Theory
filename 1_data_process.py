import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# 测试时间段，可根据数据时间更改
start_time = '20231016'
end_time = '20241223'

# 下方为数据來源
df = pd.read_csv('sh7.csv', encoding='UTF-8', skiprows=1, parse_dates=['交易日期'])
df.rename(columns={'交易日期': 'candle_end_time', '最高价': 'high', '最低价': 'low'}, inplace=True)
df['high'] = df['high'].round(2)
df['low'] = df['low'].round(2)

# 确认每行数据的编号
df['line_no'] = range(len(df))
# 只保留关键数据
df = df[['candle_end_time', 'high', 'low', 'line_no']]

# 复制一个df
df2 = df.copy()
# 创建一个保留循环结果的results
results = {}

# 遍历每根 K 线，一根根向后去找包含关系并处理
for i in df['line_no']:
    df3 = df2[df2['line_no'] == i]
    print(i)

    if i not in results:
        results[i] = pd.DataFrame()  # 创建一个空的 DataFrame
    results1 = results[i]
    df1 = pd.concat([results1, df3], ignore_index=True)

    # 确认包含关系的 K 线组
    con1 = df1['low'] <= df1['low'].shift(1)
    con2 = df1['high'].shift(1) <= df1['high']
    con3 = df1['low'].shift(1) <= df1['low']
    con4 = df1['high'] <= df1['high'].shift(1)
    df1.loc[(con1 & con2) | (con3 & con4), '包含关系'] = 1

    # 上升关系
    con5 = df1['high'].shift(2) < df1['high'].shift(1)
    con6 = df1['low'].shift(2) < df1['low'].shift(1)
    df1.loc[con5 & con6, '位置关系'] = 1
    con7 = df1['位置关系'] == 1

    # 下降关系
    con8 = df1['high'].shift(2) > df1['high'].shift(1)
    con9 = df1['low'].shift(2) > df1['low'].shift(1)
    df1.loc[con8 & con9, '位置关系'] = 0
    con10 = df1['位置关系'] == 0
    con11 = df1['包含关系'] == 1

    # 标记需要处理的K线位置，上升处理和下降处理
    df1.loc[con7 & con11, '包含处理'] = 1
    df1.loc[con10 & con11, '包含处理'] = 0

    # 合成新K线
    mask = df1['包含处理'] == 1
    df1.loc[mask, 'high'] = np.maximum(df1['high'], df1['high'].shift(1))
    df1.loc[mask, 'low'] = np.maximum(df1['low'], df1['low'].shift(1))

    mask0 = df1['包含处理'] == 0
    df1.loc[mask0, 'high'] = np.minimum(df1['high'], df1['high'].shift(1))
    df1.loc[mask0, 'low'] = np.minimum(df1['low'], df1['low'].shift(1))

    print(df1['包含处理'].iloc[-1])

    # 删除已处理K线
    if df1['包含处理'].iloc[-1] in [1, 0]:
        print(df1.iloc[-2])
        df1.drop(df1.index[-2], axis=0, inplace=True)

    # 创建新的df_new来保存数据
    df_new = df1[['candle_end_time', 'high', 'low', 'line_no']]
    results[i + 1] = df_new
    df_last = results[i + 1]

print(df_last)

# 输出预处理K线的数据文件
df_last.to_csv('数据文件1 预处理K线.csv', encoding='UTF-8')

# 创建图表
fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
fig.set_facecolor('grey')
ax.grid(False)
ax.set_facecolor('grey')
ax.spines['top'].set_edgecolor('white')
ax.spines['bottom'].set_edgecolor('white')
ax.spines['left'].set_edgecolor('white')
ax.spines['right'].set_edgecolor('white')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')

# 绘制每个交易日的最低价到最高价的线
for index, row in df_last.iterrows():
    plt.plot([row['candle_end_time'], row['candle_end_time']],
             [row['low'], row['high']], color='white', linewidth=1)

# 设置日期格式化
plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))

# 设置图表标题和轴标签
plt.xlabel('Date', color='white', fontsize=12)
plt.ylabel('Price', color='white', fontsize=12)

plt.savefig('1 K线预处理.png', dpi=100, bbox_inches='tight', pad_inches=0.1)
plt.show()