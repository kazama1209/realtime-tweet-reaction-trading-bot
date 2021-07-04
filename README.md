# realtime-tweet-reaction-trading-bot

リアルタイムで特定のユーザーのツイートに反応する仮想通貨自動売買Bot。

REST APIではなくSreaming APIを使っているため、対象ユーザーのツイートに対してより素早く反応する事ができるようになっている。

## セットアップ

環境変数をセット。

```
$ cp .env.sample .env

TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_USER_ID=
BYBIT_API_KEY=
BYBIT_API_SECRET=
```

## 動作確認

コンテナを起動。

```
$ docker-compose up -d
```

main.pyファイルを実行

```
$ docker-compose run python3 python main.py 
```

対象のユーザーが狙いの仮想通貨に関するツイートをした場合、注文が発動する。

<img width="1303" alt="スクリーンショット 2021-07-05 1 28 12" src="https://user-images.githubusercontent.com/51913879/124392394-458d7800-dd30-11eb-9b79-60e3505de7f5.png">

```
Start
-------------------------
kazama1209_bot tweeted!
Buy: 2021-07-05 01:38:15
Sell: 2021-07-05 01:43:15
-------------------------
Exit
```

