# coding=utf-8 with bom
import translate
import xlrd
import xlwt

# 打开一个workbook
workbook = xlrd.open_workbook(
    "reference.xls",  # todo 自定义
)
worksheet1 = workbook.sheets()[0]

outbook = xlwt.Workbook()  # 注意Workbook的开头W要大写
out = outbook.add_sheet("sheet1", cell_overwrite_ok=True)

cnt = 0
# 遍历sheet1中所有行row
num_rows = worksheet1.nrows
for row in range(num_rows):
    pinyin = worksheet1.cell_value(row, 1)
    char = worksheet1.cell_value(row, 0)
    if char == "" or str(char)[0] == "#":
        continue
    if pinyin == "":
        print("error", row)
        continue
    if pinyin[0] == "{":
        pinyin = pinyin[1 : len(pinyin) - 1]
    while pinyin[len(str(pinyin)) - 1] == " ":
        pinyin = pinyin[0 : len(pinyin) - 1]
    # print(char + " "+pinyin)
    out.write(cnt, 0, char)
    out.write(cnt, 1, pinyin)
    sheng = translate.pinyin_to_shengmu(pinyin)
    if sheng == "":
        sheng = "Ǿ"
    out.write(cnt, 2, sheng)
    out.write(cnt, 3, translate.pinyin_to_yunmu(pinyin))
    out.write(cnt, 4, translate.pinyin_to_tone(pinyin))
    out.write(cnt, 5, translate.pinyin_to_IPA(pinyin))
    out.write(cnt, 6, worksheet1.cell_value(row, 2))
    if translate.pinyin_to_IPA(pinyin) == "":
        print(row + " " + char)
    cnt = cnt + 1

# 保存该excel文件,有同名文件时直接覆盖
outbook.save("./target.xls")
