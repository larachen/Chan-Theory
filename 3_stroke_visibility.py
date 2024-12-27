import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)    # 最多显示数据的行数

# 测试时间段，可根据数据时间更改
start_time = '20231016'
end_time = '20241223' 

# 读取顶底分型数据
df = pd.read_csv('数据文件2 顶底分型.csv', encoding='UTF-8')

def cal_signal_keepone(df):
    df['candle_end_time'] = pd.to_datetime(df['candle_end_time'])
    
    # ==================== 数据预处理
    temp_df = df[['candle_end_time', 'high', 'low', 'signal']]
    temp_df = temp_df.sort_values(by='candle_end_time').reset_index(drop=True)
    temp_df['low'] = -temp_df['low'].shift(1)
    temp_df['high'] = temp_df['high'].shift(1)
    temp_df.loc[temp_df['signal'] == 1.0, 'price'] = temp_df['high']
    temp_df.loc[temp_df['signal'] == 0, 'price'] = temp_df['low']
    temp_df = temp_df.dropna(subset=['signal'], how="all")
    temp_df['是否保留'] = None

    # ==================== 寻找第一个保留数据
    date_begin = temp_df['candle_end_time'].iloc[0]
    
    for date in temp_df['candle_end_time']:
        signal_now = temp_df.loc[temp_df['candle_end_time'] == date, 'signal'].iloc[0]
        price_now = temp_df.loc[temp_df['candle_end_time'] == date, 'price'].iloc[0]

        # 取得开始日期的数据
        signal_begin = temp_df.loc[temp_df['candle_end_time'] == date_begin, 'signal'].iloc[0]
        price_begin = temp_df.loc[temp_df['candle_end_time'] == date_begin, 'price'].iloc[0]

        if signal_now == signal_begin:
            if price_now > price_begin:  # 更新为新价格
                temp_df.loc[temp_df['candle_end_time'] == date, '是否保留'] = 1
                break
        else:
            # Find the current index (implicitly done with .loc, no need for explicit index tracking)
            index_now = temp_df.index[temp_df['candle_end_time'] == date][0]
            index_begin = temp_df.index[temp_df['candle_end_time'] == date_begin][0]

            if (index_now - index_begin) >= 4:  # 开始日期保留
                temp_df.loc[temp_df['candle_end_time'] == date_begin, '是否保留'] = 1
                break

    # ==================== 逐行分析处理
    print(temp_df)
    
    for date in temp_df['candle_end_time']:
        print(date)
        signal_now = temp_df.loc[temp_df['candle_end_time'] == date, 'signal'].iloc[0]
        price_now = temp_df.loc[temp_df['candle_end_time'] == date, 'price'].iloc[0]

        # 取得上一个被保留日的最高、最低价
        try:
            date_before = temp_df[(temp_df['candle_end_time'] <= date) & (temp_df['是否保留'] == 1)].iloc[-1]['candle_end_time']
        except IndexError:
            continue
        
        signal_before = temp_df.loc[temp_df['candle_end_time'] == date_before, 'signal'].iloc[0]
        price_before = temp_df.loc[temp_df['candle_end_time'] == date_before, 'price'].iloc[0]

        if signal_now == signal_before and price_now > price_before:
            temp_df.loc[temp_df['candle_end_time'] == date, '是否保留'] = 1
        elif (temp_df.index[temp_df['candle_end_time'] == date][0] - 
              temp_df.index[temp_df['candle_end_time'] == date_before][0]) >= 4:
            temp_df.loc[temp_df['candle_end_time'] == date, '是否保留'] = 1

    temp_df = temp_df[temp_df['是否保留'] == 1]
    temp_df.rename(columns={'signal': 'signal_保留'}, inplace=True)
    temp_df_final = temp_df[(temp_df['signal_保留'] - temp_df['signal_保留'].shift(-1)) != 0]
    temp_df_final.rename(columns={'signal_保留': 'signal_最终保留'}, inplace=True)

    # 合并信号
    df = pd.merge(df, temp_df[['candle_end_time', 'signal_保留']], how='left', on='candle_end_time')
    df = pd.merge(df, temp_df_final[['candle_end_time', 'signal_最终保留']], how='left', on='candle_end_time')
    
    return df

if __name__ == '__main__':
    df['candle_end_time'] = pd.to_datetime(df['candle_end_time'])
    df = cal_signal_keepone(df)
    print(df[['candle_end_time', 'high', 'low', 'signal', 'signal_保留', 'signal_最终保留']].head(1000))

# 处理信号价格
df['笔的信号'] = df['signal_最终保留']
df.loc[df['signal_最终保留'] == 1, '笔的价格'] = df['high'].shift(1)
df.loc[df['signal_最终保留'] == 0, '笔的价格'] = df['low'].shift(1)
df['画图信号点'] = df['笔的价格'].shift(-1)

df.to_csv('数据文件3 笔.csv', encoding='UTF-8')

# 选择画图的时间范围
df = df[(df['candle_end_time'] >= pd.to_datetime(start_time)) & 
         (df['candle_end_time'] <= pd.to_datetime(end_time))]

# 创建图和轴
fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
fig.set_facecolor('grey')

# 设置图层颜色和边框
ax.set_facecolor('grey')
ax.spines['top'].set_edgecolor('white')
ax.spines['bottom'].set_edgecolor('white')
ax.spines['left'].set_edgecolor('white')
ax.spines['right'].set_edgecolor('white')

# 设置刻度标记的颜色
ax.tick_params(axis='x', colors='white')  # 设置x轴刻度标记颜色为白色
ax.tick_params(axis='y', colors='white')  # 设置y轴刻度标记颜色为白色

# 绘制K线图
for idx, row in df.iterrows():
    if pd.notna(row['candle_end_time']) and pd.notna(row['high']) and pd.notna(row['low']):
        ax.plot([mdates.date2num(row['candle_end_time']), mdates.date2num(row['candle_end_time'])],
                [row['low'], row['high']], color='white', linewidth=1)

# 添加箭头
previous_point = None
for i in range(len(df)):
    if pd.notna(df['candle_end_time'].iloc[i]) and pd.notna(df['画图信号点'].iloc[i]):
        current_point = (mdates.date2num(df['candle_end_time'].iloc[i]), df['画图信号点'].iloc[i])

        if previous_point is not None:
            dx = current_point[0] - previous_point[0]
            dy = current_point[1] - previous_point[1]
            ax.arrow(previous_point[0], previous_point[1], dx, dy,
                     head_width=0, head_length=0, fc='orange', ec='orange', linewidth=2)

        previous_point = current_point

# 设置日期格式
ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=20))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))

# 设置网格和标签
ax.grid(False)  # 关闭网格
plt.xticks(rotation=0, color='white', fontsize=12)  # 设置x轴刻度标签颜色和大小
plt.yticks(color='white', fontsize=12)  # 设置y轴刻度标签颜色和大小
plt.xlabel('Date', color='white', fontsize=12)  # 设置x轴标签颜色和大小
plt.ylabel('Price', color='white', fontsize=12)  # 设置y轴标签颜色和大小

# 保存图形，指定分辨率和大小
plt.savefig('3 Stroke Visibility.png', dpi=100, bbox_inches='tight', pad_inches=0.1)

plt.show()