#   单字文件预处理
import xlrd
import xlwt

workbook = xlrd.open_workbook("1.xls")
worksheet = workbook.sheets()[0]

outbook = xlwt.Workbook()
out = outbook.add_sheet("sheet1", cell_overwrite_ok=True)

cnt = 0

num_rows = worksheet.nrows
for row in range(num_rows):
    char = worksheet.cell_value(row, 1)
    pinyin = worksheet.cell_value(row, 2)
    ipa = worksheet.cell_value(row, 3)
    pinyin_list = pinyin.split(" ")
    ipa_list = ipa.split(" ")
    for i in range(len(pinyin_list)):
        if (pinyin_list[i] == ""):
            continue
        out.write(cnt, 0, char)
        out.write(cnt, 1, pinyin_list[i])
        out.write(cnt, 2, ipa_list[i])
        cnt = cnt + 1

outbook.save("./11.xls")