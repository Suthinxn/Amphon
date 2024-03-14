import pandas as pd

# โหลดข้อมูลจากไฟล์ CSV แรก
df1 = pd.read_csv('/home/suthinan/Learning/Freshman/Term02/Basic_Ai/dash_project/Amphon/prediction_pm/predictions_temp.csv')

# โหลดข้อมูลจากไฟล์ CSV ที่สอง
df2 = pd.read_csv('/home/suthinan/Learning/Freshman/Term02/Basic_Ai/dash_project/Amphon/prediction_pm/predictions_pm25.csv')

# รวมข้อมูลด้วย pd.concat() (รวมแถว)
merged_df = pd.concat([df1, df2])



# merged_df.to_csv('pre3PM25.csv', index=False)

# รวมข้อมูลด้วย pd.merge() (รวมคอลัมน์โดยใช้คีย์)
merged_df = pd.merge(df1, df2, on='DATETIMEDATA')
merged_df.to_csv('merged_data.csv', index=False)