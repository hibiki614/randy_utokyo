- 最大値が欲しい時
~~~
lambda = lambda + theta*y
    for i in range(len(lambda)):
        if lambda[i] >= 0:
            lambda[i] = lambda[i]
        else:
            lambda[i] = 0
~~~
ではなくて
~~~
lagrange_multipliers = [max(0, lm) for lm in lagrange_multipliers]
~~~
のようにmax()を用いれば一発で書ける
lambdaはpythonのキーワードとして使われるのでつかわないほうがいい

## エラーの種類について
https://www.kikagaku.co.jp/kikagaku-blog/python-basic-error/#i-2


## お役立ちサイト
- python Japanの入門講座
- https://www.python.jp/train/index.html