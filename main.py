import tweepy
import datetime
from time import sleep
import os
from dotenv import load_dotenv
load_dotenv()
from bybit_api import BybitAPI

# 狙いの通貨名（表記ゆれを考慮して複数指定）
target_coin_names = [
    'ビットコイン',
    'bitcoin',
    'btc'
]

# 買い要因になりそうな単語（表記ゆれを考慮して複数指定）
positive_words = [
    '買い',
    'buy',
    'moon'
]

# 売り要因になりそうな単語（表記ゆれを考慮して複数指定）
negative_words = [
    '売り',
    'sell'
]

# Bybit API
bybit_api = BybitAPI()

# 取引したい通貨ペア
symbol = 'BTC/USD'

# 注文量（USD）
amount = 1

# エントリーフラグ
entry_flag = False

# ツイート本文中に狙いの通貨名（条件1）＋買い要因or売り要因の単語（条件2）が含まれるかを確認してエントリーの方向性を判断
# 条件1と条件2は必ずセットである必要があり、どちらか片方だけでは成立しない
# ex) ビットコイン 買い
def judge_entry_side(tweet_text):
	# 買い要因と売り要因、両方の単語が含まれていた場合は判断に困るので待機
	if any([target_coin_name in tweet_text for target_coin_name in target_coin_names]) \
		and any([positive_word in tweet_text for positive_word in positive_words]) \
		and any([negative_word in tweet_text for negative_word in negative_words]):
		
		return "stay"

	# 買い要因の単語が含まれていた場合は買い
	elif any([target_coin_name in tweet_text for target_coin_name in target_coin_names]) \
		and any([positive_word in tweet_text for positive_word in positive_words]):

		return "buy"
	
	# 売り要因の単語が含まれていた場合は売り
	elif any([target_coin_name in tweet_text for target_coin_name in target_coin_names]) \
		and any([negative_word in tweet_text for negative_word in negative_words]):

		return "sell"
	
	# それらしい単語が含まれていなかった場合も待機
	else:
		return 'stay'

class StreamListener(tweepy.StreamListener):
	# 対象のユーザーが新規にツイートをするたびにこの関数が走る
	def on_status(self, status):
		global entry_flag

		# 現在時刻を算出
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		# 未エントリーだった場合のみ以降の処理を行う
		if entry_flag == False:
			# ツイートの種類をチェック（リツイート or リプライ or 通常）
			tweet_type = self.check_tweet_type(status)
			
			# 通常のツイート以外（リツイートやリプライ）だった場合はここで終了
			if tweet_type != 'normal':
				return
			
			# ツイート本文（単語チェックしやすいように小文字に変換）
			tweet_text = status.text.lower()

			# ツイート本文中に狙いの通貨名（条件1）＋買い要因or売り要因の単語（条件2）が含まれるかを確認してエントリーの方向性を判断
			entry_side = judge_entry_side(tweet_text)

			# 買い判断が出た場合は買い注文を出す
			if entry_side == 'buy':
				# 成り行き買い注文
				order = bybit_api.create_order(symbol, 'market', 'buy', amount)
				print(f'Buy: {now}')

				# エントリーフラグをTrueに変更
				entry_flag = True

				# 注文が済んだらStreamListenerを停止（構造的には「while True〜」で動いているのでFalseを返せば停止する）
				return False

			# 売り判断が出た場合は売り注文を出す
			elif entry_side == 'sell':
				# 成り行き売り注文
				order = bybit_api.create_order(symbol, 'market', 'sell', amount)
				print(f'Sell: {now}')

				# エントリーフラグをTrueに変更
				entry_flag = True

				# 注文が済んだらStreamListenerを停止（構造的には「while True〜」で動いているのでFalseを返せば停止する）
				return False
			
			# 待機判断が出た場合は何もしない
			else:
				pass

	# ツイートの種類をチェック（リツイート or リプライ or 通常）
	def check_tweet_type(self, status):
		# JSON内のキーに「retweeted_status」があればリツイート
		if 'retweeted_status' in status._json.keys():
			return 'retweet'
		
		# 「in_reply_to_user_id」がNoneでなかった場合はリプライ
		elif status.in_reply_to_user_id != None:
			return 'reply'

		# それ以外は通常のツイート
		else:
			return 'normal'

# 認証
api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

stream_listener = StreamListener()
stream = tweepy.Stream(auth = auth, listener = stream_listener)

# 監視開始
print('Start')
print('-------------------------')

# 監視対象のユーザーID（https://idtwi.com/ ←参照）
twitter_user_id = os.getenv('TWITTER_USER_ID')

# ユーザーIDは配列で複数渡す事が可能
# もし別のスレッドで処理を行わせたい場合はfilterの引数に「is_async = True」を渡す
stream.filter(follow=[twitter_user_id])

# エントリー後に行う処理（もし早期決済を行いたくない場合（ガチホ予定など）はコメントアウトでOK）
if entry_flag == True:
	# sleepには決済までの秒数を指定する
	sleep(300)

	# 現在時刻を算出
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	# 自分のポジション状況を確認
	position = bybit_api.get_position(symbol)

	# 買いポジションを持っていた場合は同量の売り注文を出す
	if position['side'] == 'Buy':
		order = bybit_api.create_order(symbol, 'market', 'sell', amount)
		print(f'Sell: {now}')
	
	# 売りポジションを持っていた場合は同量の買い注文を出す
	elif position['side'] == 'Sell':
		order = bybit_api.create_order(symbol, 'market', 'buy', amount)
		print(f'Buy: {now}')
	
	# 何かの間違いで万が一ノーポジだった場合は何もしない
	else:
		pass

# 監視終了
print('-------------------------')
print('Exit')
