# -*-coding:utf-8-*-


def isconnect(a, b):
    return a[1] == b[0] - 1


def split_ipa_from_mp3(music, chunks=1):
    DBFS = [db.dBFS for db in music[:]]
    n = len(DBFS)
    a = sorted(enumerate(DBFS), reverse=True, key=lambda a: a[1])
    mean = a[int(n * 0.85)][1]
    num = 0.3 * len(DBFS)
    strip = 0.1 * len(DBFS) / chunks
    d = [[a[0][0], a[0][0]]]
    j = 1
    for i in range(1, chunks):
        while j < len(DBFS):
            t = 0
            for x, y in d:
                if x - strip < a[j][0] < y + strip:
                    t = 1
                    break
            if not t:
                d.append([a[j][0], a[j][0]])
                break
            j += 1
    d.sort(key=lambda a: a[0])
    while num > 0:
        t = num
        for i in range(chunks):
            if max(DBFS[d[i][0] - 1], DBFS[d[i][1] + 1]) >= mean:
                if DBFS[d[i][0] - 1] >= DBFS[d[i][1] + 1] and (
                    ~i or not isconnect(d[i - 1], d[i])
                ):
                    d[i][0] -= 1
                    num -= 1
                elif DBFS[d[i][0] - 1] <= DBFS[d[i][1] + 1] and (
                    i == chunks - 1 or not isconnect(d[i], d[i + 1])
                ):
                    d[i][1] += 1
                    num -= 1
        if t == num:
            break
    return d
