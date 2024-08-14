def find_first(arr: list, search_fun):
    answer = None
    for i in arr:
        if search_fun(i):
            answer = i
    return answer
