import re


def pinyin_to_tone(pinyin):
    try:
        matchObj = re.match(r"([a-z|ⁿ]+)([0-9]*)$", pinyin, re.M | re.I)
        return matchObj.group(2)
    except Exception:
        print("[寻找声调]这不是一个合法的拼音: ", pinyin)
        return None


def pinyin_to_shengmu(pinyin):
    try:
        matchObj = re.match(r"([a-z|ⁿ]+)([0-9]*)$", pinyin, re.M | re.I)
        line = matchObj.group(1)  # 获取非声调部分
        matchObj = re.match(r"(ng?|[^aeiouy]?)(.*)$", line, re.M | re.I)
        sheng = matchObj.group(1)
        if line == "ng":
            sheng = ""  # 特殊情况
        return sheng
    except Exception:
        print("[寻找声母]这不是一个合法的拼音: ", pinyin)
        return None


def pinyin_to_yunmu(pinyin):
    try:
        matchObj = re.match(r"([a-z|ⁿ]+)([0-9]*)$", pinyin, re.M | re.I)
        line = matchObj.group(1)  # 获取非声调部分
        matchObj = re.match(r"(ng?|[^aeiouy]?)(.*)$", line, re.M | re.I)
        yun = matchObj.group(2)
        if line == "ng":
            yun = "ng"  # 特殊情况
        return yun
    except Exception:
        print("[寻找韵母]这不是一个合法的拼音: ", pinyin)
        return None


def pinyin_to_IPA(pinyin):
    try:
        sheng = pinyin_to_shengmu(pinyin)  # 声母
        yun = pinyin_to_yunmu(pinyin)  # 韵母
        tone = pinyin_to_tone(pinyin)  # 声调
        matchObj = re.match(r"(.*?)(ng?|n?|h?|ⁿ?)$", yun, re.M | re.I)
        yun1 = matchObj.group(1)  # 韵母元音
        yun2 = matchObj.group(2)  # 韵尾

        # 声母的处理
        if sheng == "b":
            sheng = "p"
        elif sheng == "p":
            sheng = "ph"
        elif sheng == "d":
            sheng = "t"
        elif sheng == "t":
            sheng = "th"
        elif sheng == "z":
            sheng = "ts"
        elif sheng == "c":
            sheng = "tsh"
        elif sheng == "g":
            sheng = "k"
        elif sheng == "k":
            sheng = "kh"
        elif sheng == "s":
            sheng = "ɬ"
        elif sheng == "ng":
            sheng = "ŋ"
        elif sheng == "":
            sheng = ""  # 零声母Ǿ

        # 开尾韵或鼻化韵的处理
        if yun2 == "" or yun2 == "n":
            if yun1 == "ae":
                yun1 = "ɛ"
            elif yun1 == "oe":
                yun1 = "ø"
            elif yun1 == "or":
                yun1 = "ɒ"
            elif yun1 == "ou":
                yun1 = "ɔu"
            elif yun1 == "yor":
                yun1 = "yɒ"

        # 塞尾韵或鼻尾韵的处理
        if yun2 == "h" or yun2 == "ng":
            # 元音部分
            if yun1 == "e":
                yun1 = "ɛ"
            elif yun1 == "ie":
                yun1 = "iɛ"
            elif yun1 == "oe":
                yun1 = "œ"
            elif yun1 == "o":
                yun1 = "ɔ"
            elif yun1 == "or":
                yun1 = "ɒ"
            elif yun1 == "yor":
                yun1 = "yɒ"
            # 韵尾部分
            if yun2 == "ng":
                yun2 = "ŋ"
            elif yun2 == "h":
                yun2 = "ʔ"
            elif yun2 == "ⁿ":
                yun2 = "ⁿ"

        # 声调的处理
        if tone == "1":
            tone = "533"
        elif tone == "2":
            tone = "13"
        elif tone == "3":
            tone = "453"
        elif tone == "4":
            tone = "42"
        elif tone == "5":
            tone = "11"
        elif tone == "6":
            tone = "21"
        elif tone == "7":
            tone = "4"

        return str(sheng + yun1 + yun2 + tone)
    except Exception:
        print("[翻译IPA]这不是一个合法的拼音: ", pinyin)
        return None


def mohuyin(pinyin):
    result = set()
    try:
        sheng = pinyin_to_shengmu(pinyin)  # 声母
        yun = pinyin_to_yunmu(pinyin)  # 韵母
        tone = pinyin_to_tone(pinyin)  # 声调

        # 对于声母的处理
        if sheng == "j":
            sheng = {"z"}
        elif sheng == "q":
            sheng = {"c"}
        elif sheng == "x":
            sheng = {"s"}
        else:
            sheng = {sheng}

        # 对于声调的处理
        if tone == "":
            if yun[-1] == "h":
                tone = {"6", "7"}
            else:
                tone = {"1", "2", "3", "4", "5"}
        else:
            tone = {tone}
        # 对于韵母的处理
        if yun == "ie":
            yun = {"ia"}
        elif yun == "yoe":
            yun = {"yor"}
        elif yun == "uei" or yun == "ua" or yun == "uai":
            yun = {"ue"}
        elif yun == "iau" or yun == "ieo" or yun == "iao":
            yun = {"ieu"}
        elif yun == "uo":
            yun = {"ua"}
        elif yun == "ao":
            yun = {"au"}
        elif yun == "ou" or yun == "o":
            yun = {"o", "ou"}
        elif yun == "erh":
            yun = {"oh"}
        elif yun == "ieng" or yun == "eng":
            yun = {"ieng", "eng"}
        elif yun == "erng":
            yun = {"ong", "oeng", "yorng"}
        elif sheng in {"z", "c", "s"} and yun == "u":
            yun = {"y"}
        elif yun in {"ei"}:
            yun = {"e"}
        else:
            yun = {yun}

        # 声韵调的组合
        for s in sheng:
            for y in yun:
                for t in tone:
                    result.add(str(s + y + t))

    except Exception as e:
        print(e.with_traceback)
        print("[寻找模糊音]这不是一个合法的拼音: ", pinyin)

    return result


# 一些测试数据
pinyin = [
    "buai1",
    "dei3",
    "lyorng2",
    "nguai1",
    "a4",
    "loe2",
    "ng2",
    "heng2",
    "meh3",
    "tatfd",
    "ah7",
    "sing2",
    "ngorng5",
    "gyorng2",
    "leh6",
    "ki4",
    "nang1",
    "gerng1",
    "keh",
]
for s in pinyin:
    print("拼音： ", s)
    m = mohuyin(s)
    print("模糊音： ", m)
    mm = set()
    for p in m:
        mm.add(pinyin_to_IPA(p))
    print("模糊音IPA：", mm)
    print()
