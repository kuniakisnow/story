---
layout: post
title: "分散ストレージ ― CephとMinIOで実現するスケールアウトの世界"
date: 2026-07-06 09:00:00 +0900
tags: [storage, distributed, ceph, minio, object-storage]
description: "分散ストレージの代表格CephとMinIOを中心に、アーキテクチャ、Erasure Coding、S3互換API、ハードウェア構成まで解説します。"
---

梅雨明け間近の蒸し暑い金曜午後。新人君がサーバルームの温度計を睨みながら、NASの容量アラート通知がひっきりなしに鳴るスマートフォンを手に、先輩のデスクに駆け寄った。

「先輩、NASの空き容量がやばいです！あと2%で満杯って警告が出てます。それに、同じファイルを20人で同時に編集しようとしたら、みんなの操作がカクカクになってました」

『お、来た来た。ちょうどいいタイミングだ。この前<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>アレイの話をしただろ。実はNASの限界が来てるんだよ。そこでな、今日は**分散ストレージ**の話をしようと思ってたんだ。』

「分散ストレージ？NASじゃないんですか？」

『NASは**スケールアップ**っていって、筐体を大きくするか、より高性能な箱に載せ替えるしか拡張方法がない。一方**分散ストレージ**は**スケールアウト**、つまり普通のサーバを横に並べて、それらを束ねて一つのストレージに見せるんだ。』

「サーバを束ねる…って、それってどうやってるんですか？」

『代表格が二つあってな。<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>と<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>だ。まず<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>から行こう。<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>は<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>っていうコア技術が全ての基盤になってる。』

「<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>ってなんですか？」

『<ruby>Reliable Autonomic Distributed Object Store<rp>《</rp><rt>リライアブルオートノミックディストリビューテッドオブジェクトストア</rt><rp>》</rp></ruby>の略だ。要するに「自分で自分を管理できる信頼性の高い分散オブジェクトストア」って意味だ。この<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>の上に3つのインターフェースが乗ってる。』


先輩はホワイトボードに3階建ての図を描き始めた。

『一番上が三つに分かれてる。<ruby>RBD<rp>《</rp><rt>アールビーディー</rt><rp>》</rp></ruby>がブロックストレージ、<ruby>RGW<rp>《</rp><rt>アールジーダブリュー</rt><rp>》</rp></ruby>がS3互換の<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>、<ruby>CephFS<rp>《</rp><rt>セフエフエス</rt><rp>》</rp></ruby>がファイルストレージだ。この3つが全部、一本の<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>クラスタの上で動く。』

「え、<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>もオブジェクトもファイルも、一つのクラスタで同時に提供できるってことですか？」

『そうだ。これが<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の最大の強みだ。普通は<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>用、ファイル用、オブジェクト用で別々のストレージを用意するものだが、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>は全部一本化できる。VMのブロックボリュームも、コンテナのイメージレジストリも、ホームディレクトリのファイル共有も、全部同じクラスタで賄える。』

「でもそれってすごいリスクじゃないですか？全部が同じクラスタだと、障害時に全滅しません？」

『そこが<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の設計思想の肝だ。すべては<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>の**自己修復機能**で守られてる。そしてデータをどこに置くかを決めるのが<ruby>CRUSHアルゴリズム<rp>《</rp><rt>クラッシュアルゴリズム</rt><rp>》</rp></ruby>だ。』

「CRUSH？なんか変な名前ですね」

『<ruby>Controlled Replication Under Scalable Hashing<rp>《</rp><rt>コントロールドレプリケーションアンダースケーラブルハッシング</rt><rp>》</rp></ruby>の略だ。日本語にすると「スケーラブルなハッシュによる制御された複製」。これが従来の分散ストレージと一線を画す、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>最大の特徴だ。』

「ふーん…普通の分散ストレージと何が違うんですか？」

『従来の分散ストレージは、たいてい**メタデータサーバ**っていう「このデータはどこにあるよ」を管理する中央サーバが必要だった。これがスケーラビリティのボトルネックになるし、単一障害点にもなる。<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のCRUSHはクライアント側の計算だけで「このデータはこの<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>」と決定できる。メタデータサーバが不要なんだ。』

「クライアント側だけで？それってどういう仕組みなんですか？」

『CRUSHマップというクラスタのトポロジ情報を全クライアントが持ってる。例えば「ルームAのラック3に入ってるホスト5台の中の、<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>番号7と12と23だな」って計算する。この計算が決定的で、かつデータが均等に散るようにハッシュ関数で制御されてる。クラスタにノードを追加しても、移動するデータ量は全体のごく一部だけだ。』

「なるほど…メタデータサーバに聞かなくても、自分で計算できるからボトルネックがないんですね。でもそれだけだとデータの信頼性はどう保つんですか？」

『そこで登場するのが<ruby>Placement Group<rp>《</rp><rt>プレースメントグループ</rt><rp>》</rp></ruby>、通称<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>だ。<ruby>RADOS<rp>《</rp><rt>ラドス</rt><rp>》</rp></ruby>はデータをオブジェクト単位で管理するが、そのオブジェクトを<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>というグループにまとめる。そして<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>単位でレプリカや<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>を適用する。』

「<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>…聞いたことあります！RAIDのパリティみたいなやつですよね？」

『似ているが、もっと柔軟で強力だ。k+mのパラメータで、k個のデータチャンクに対してm個のパリティチャンクを作る。例えば8+3なら、11台の<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>にデータを分散して、そのうち最大3台が同時に死んでもデータは復元できる。』

「3台同時障害まで耐えられる…すごい<ruby>冗長性<rp>《</rp><rt>じょうちょうせい</rt><rp>》</rp></ruby>ですね。でもそれってオーバーヘッドはどうなんですか？3-wayレプリケーション（3重化）と比べて？」

『いい質問だ。3-wayレプリケーションは200%のオーバーヘッド（データ1に対して保存量3）、つまり3倍の容量が必要だ。一方<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby> 8+3なら、データ1に対して保存量は11/8で約1.375倍だ。容量効率は大幅に良い。』

「じゃあ全部<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>で良くないですか？」

『そう簡単じゃない。<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>は計算コストがかかるし、書き込みのレイテンシが増える。特に小さなランダム書き込みは苦手だ。だから最近のベストプラクティスは、ホットデータは3-wayレプリケーションで書き込んで、コールドデータを自動で<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>に変換する階層管理だ。』

「なるほど…使い分けが大事ってことですね。それで、さっき言ってたWAL/<ruby>DB<rp>《</rp><rt>データベース</rt><rp>》</rp></ruby>ってなんですか？」

『<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>はBlueStoreっていうストレージエンジンを使ってる。BlueStoreはRocksDB（<ruby>LSM<rp>《</rp><rt>エルエスエム</rt><rp>》</rp></ruby>-TreeベースのKVS）でメタデータを管理して、実際のデータは直接ブロックデバイスに書き込む。この時、RocksDBのWAL（Write Ahead Log）と<ruby>DB<rp>《</rp><rt>データベース</rt><rp>》</rp></ruby>領域には高速な<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>を使い、データ領域には大容量<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>を使う構成が推奨されてるんだ。』

「<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>と<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>のハイブリッド…ちょうど先週やった<ruby>AFA<rp>《</rp><rt>エーエフエー</rt><rp>》</rp></ruby>の<ruby>QLC<rp>《</rp><rt>クアッドレベルセル</rt><rp>》</rp></ruby>/<ruby>TLC<rp>《</rp><rt>トリプルレベルセル</rt><rp>》</rp></ruby>階層と似てますね」

『そう。OSD1台につきWAL/<ruby>DB<rp>《</rp><rt>データベース</rt><rp>》</rp></ruby>用に<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>を割り当てて、データ用に6〜12台の<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>をぶら下げる。HDD1台あたりの推奨は6〜14TB、回転数は7200rpmで、SASよりSATAの方がコスト面で推奨されることが多い。』

「<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>とメモリはどのくらい必要なんですか？」

『<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>ホスト1台でざっくりこんな感じだ。<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>は<ruby>AMD<rp>《</rp><rt>エーエムディー</rt><rp>》</rp></ruby> EPYCか<ruby>Intel<rp>《</rp><rt>インテル</rt><rp>》</rp></ruby> Xeonで16〜32コア。メモリはOSD1台あたり4〜8GB、プラスホストあたり32GBのベース。つまり<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>を12台積むなら、32＋12×4＝80GBってところだ。ネットワークは10GbE以上、最近は25GbEか100GbEが当たり前になってきてる。』

「結構リソース食うんですね…でもちゃんと設計すれば信頼性と容量の両立ができるわけか。じゃあ次に<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の方はどうなんですか？」

『<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>と設計思想が真逆だ。<ruby>Go言語<rp>《</rp><rt>ゴーげんご</rt><rp>》</rp></ruby>で書かれた、めちゃくちゃ軽量なS3互換<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>で、何より**シンプルさ**が売りだ。』

「<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>よりシンプルってことですか？」

『そう。<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>は1つのクラスタで<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>もファイルもオブジェクトも全部やるオールインワン。対して<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>に特化してる。機能をS3 APIだけに絞って、コードベースを極限まで小さくしてるんだ。実行バイナリはたったの100MB以下だぞ。』

「100MB？！<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のインストールサイズが何<ruby>GB<rp>《</rp><rt>ギガバイト</rt><rp>》</rp></ruby>もあるのと比べると桁違いですね。でもそれでちゃんと動くんですか？」

『そのシンプルさこそが<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の武器だ。シングルバイナリで、起動も速い。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>との統合も抜群で、Helmチャート一発でクラスタが組める。各Podに<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>サーバをデプロイして、<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>で管理する。』

「<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>ネイティブってわけですね。S3互換ってのも大きいですよね。AWS S3のAPIをそのまま使えるから、既存のS3 SDKでアクセスできる」

『そう。アプリケーション側はS3エンドポイントを<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>に切り替えるだけでいい。<ruby>バケット<rp>《</rp><rt>バケット</rt><rp>》</rp></ruby>もオブジェクトもそのまま扱える。さらに<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は**マルチサイト構成**で地理分散もできる。アクティブ/アクティブのレプリケーションで、東京と大阪のクラスタ間でデータを自動同期できるんだ。』

「災害対策にも強いと。でもそれならもう<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>はいらないんじゃ…」

『待て待て。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>はあくまで<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>だけだ。ブロックストレージは提供しない。だからVMの起動ディスクやデータベースのRawデバイスが欲しいなら、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby> <ruby>RBD<rp>《</rp><rt>アールビーディー</rt><rp>》</rp></ruby>が必要になる。逆に、単にS3互換の<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>が欲しいだけなら、<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の方がはるかに導入が簡単だ。』

「じゃあ使い分けなんですね。大規模で<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>もファイルもS3も一本化したいなら<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>、とにかくシンプルにS3を使いたいなら<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>」

『その通り。選定基準としてよく使われるのは、まず容量規模だ。<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>はPB級、数十台以上の大規模クラスタに向いてる。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は<ruby>TB<rp>《</rp><rt>テラバイト</rt><rp>》</rp></ruby>〜PBまでだが、特に100TB未満の中小規模や、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>上のコンテナワークロードとの親和性が高い。』

「でもそれだけじゃなくて、<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>の好みもありますよね？<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>は設定項目がとにかく多くて、<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>の追加や<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>のチューニングとか、ちゃんと理解してないと事故るって聞きました」

『そう。CRUSHマップの変更を間違えるとデータが吹っ飛ぶ。だから<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>にはある程度の経験が必要だ。対して<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は設定が極めてシンプルで、<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>の敷居が低い。ただし、<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>のストレージ効率や拡張性の面では、大規模になるほど<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>に軍配が上がる。』

「なるほど…ところで、この前AWSの<ruby>S3 Glacier<rp>《</rp><rt>エススリーグレイシャー</rt><rp>》</rp></ruby>みたいなアーカイブ用途には使えるんですか？」

『どちらもS3互換だから、ライフサイクルポリシーを組める。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>にはバケット単位で<ruby>WORM<rp>《</rp><rt>ワーム</rt><rp>》</rp></ruby>（Write Once Read Many）も設定できる。ただしGlacier完全互換ではないから、テープ相当のコールドストレージが必要なら、別途アーカイブ用の階層を考える必要がある。』

「<ruby>WORM<rp>《</rp><rt>ワーム</rt><rp>》</rp></ruby>？それってコンプライアンス要件で必要なやつですよね。金融機関とかでデータを絶対に改ざんできないようにする」

『その通り。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>はデフォルトでオブジェクトのイミュータビリティをサポートしてる。これは<ruby>Object Lock<rp>《</rp><rt>オブジェクトロック</rt><rp>》</rp></ruby>と呼ばれる機能で、一度書き込んだオブジェクトを指定期間中は削除も変更もできなくする。SEC Rule 17a-4などの規制要件を満たせる。』

「<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>にもあるんですか？」

『<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby> <ruby>RGW<rp>《</rp><rt>アールジーダブリュー</rt><rp>》</rp></ruby>にも<ruby>Object Lock<rp>《</rp><rt>オブジェクトロック</rt><rp>》</rp></ruby>機能はある。ただし<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の方が実装がシンプルで、ドキュメントも充実してる。あと、<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の特徴として**<ruby>バケット<rp>《</rp><rt>バケット</rt><rp>》</rp></ruby>単位の暗号化**（SSE-S3）や**KMS統合**（<ruby>Hashicorp Vault<rp>《</rp><rt>ハシコープボールト</rt><rp>》</rp></ruby>など）もサポートしてる。』

「じゃあ、本番ではどっちを選べばいいんですか？」

『「どっちが良いか」じゃなくて「どっちが適してるか」を考えるんだ。例えば―』

先輩は手帳に表を書き始めた。

『<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>が有利なケース：ブロックストレージ（<ruby>RBD<rp>《</rp><rt>アールビーディー</rt><rp>》</rp></ruby>）が必要、Cinder/Glanceと統合したいOpenStack環境、PB超の大規模クラスタ、ブロック・ファイル・オブジェクトの全部入りが必要なケース。』

『<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>が有利なケース：<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>ネイティブ環境、純粋なS3互換ストレージだけ欲しい、軽量・簡易運用が最優先、<ruby>AI/ML<rp>《</rp><rt>エーアイエムエル</rt><rp>》</rp></ruby>のデータレイク用途、エッジからクラウドまでの一貫したS3 APIが欲しい。』

「なるほど…状況に応じて選ぶんですね。でもちょっと待ってください。この前までNASの限界に悩んでたのに、突然<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>と<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>って候補が2つも出てきて、どっちもNASよりずっと柔軟でスケーラブルじゃないですか！容量不足も性能問題も、どっちかを選べば解決できるってことですか？」

『お、やっと気づいたか。そうだ。NASは高性能だが拡張性に限界がある。分散ストレージは、ノードを追加するだけで容量も性能もリニアに拡張できる。これは**単一障害点（SPOF）が一切ない**設計でもある。どのノードが死んでも、クラスタ全体は止まらない。』

「あ、今すごい大事なこと言いましたね。NASの筐体のコントローラが死んだら終わりですもんね。でも分散ストレージはノードが1台死んでも、他のノードがカバーする」

『そう。さらにスケールアウトするたびに性能も上がる。NASは筐体の上限が性能の上限だが、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>も<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>もノードを増やすほどIOPSもスループットも増える。これがスケールアウトの真の価値だ。』

「でも、待ってください。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>ってシングルバイナリで軽量って言いましたけど、本当にエンタープライズで使えるんですか？某NASベンダーみたいに、画面がちゃんとしてるとか、サポートが手厚いとか、そういうのも重要じゃないですか？」

『<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は <ruby>Enterprise<rp>《</rp><rt>エンタープライズ</rt><rp>》</rp></ruby> 向けに <ruby>SUBNET<rp>《</rp><rt>サブネット</rt><rp>》</rp></ruby> っていう有償サポートを提供してる。24時間365日の電話サポート、SLA保証、セキュリティアラートの通知、独自のライセンスモデルで<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>される。もちろん<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>にも <ruby>Red Hat<rp>《</rp><rt>レッドハット</rt><rp>》</rp></ruby> <ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby> Storage や <ruby>Canonical<rp>《</rp><rt>カノニカル</rt><rp>》</rp></ruby> Charmed <ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby> の有償サポートがある。』

「両方ともコミュニティエディションとエンタープライズ版があるわけですね。じゃあもうNASを捨てて全部<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>に移行します！」

『ちょっと待て。分散ストレージは万能じゃない。小さなファイルが大量にあると、<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>はメタデータのオーバーヘッドで性能が出ない。特に<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>は4KiBのような小さなオブジェクトが大量にある用途には向かない。また、NASで動いてたActive Directory統合のファイルロック機能は、<ruby>CephFS<rp>《</rp><rt>セフエフエス</rt><rp>》</rp></ruby>でも完全互換とはいかない。』

「なるほど…向き不向きがあるんですね」

『だから、まずは要件をちゃんと整理するんだ。今のNASでやってる業務を全部リストアップして、<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>が必要か、ファイルが必要か、S3で足りるか。それから適切なストレージを選ぶ。場合によっては、NAS + <ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby> + <ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>の**ハイブリッド**が正解かもしれない。』

「ハイブリッド…<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに全部が全部分散ストレージに載せ替える必要はないですね。ホットデータはNASのまま並べ替えて、アーカイブは<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>に、外部連携S3は<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>に、みたいな」

『良い判断だ。ただし、間違ってもNASや分散ストレージを「ただ買ってきて繋ぐ」だけではダメだ。ちゃんと運用設計、監視設計、障害対応のオペレーションまで考えて導入しないと、数年後には今と同じ問題で頭を抱えることになる。』

「運用設計…<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに言われてみればそうですよね。ストレージって買うだけじゃなくて、使い続けるための仕組みが重要なんですね」

『そういうことだ。さあ、今すぐNASのアラートを止めて、並行して本番環境のワークロード分析と、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のラボ構築を始めよう。』

「ラボ？ラボって何ですか？」

『物理サーバがなくても、 <ruby>Vagrant<rp>《</rp><rt>ベイグラント</rt><rp>》</rp></ruby> とか <ruby>VirtualBox<rp>《</rp><rt>バーチャルボックス</rt><rp>》</rp></ruby> で<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のミニクラスタくらい組める。まずは組んで壊してを繰り返して、CRUSHマップの変更練習と<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>のバランシングを体で覚えろ。』

「はい！早速やってみます！」

（こうして新人君は、NASという単一筐体の限界を痛感した。その上で、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>と<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>という分散ストレージのアーキテクチャを学び、スケールアウトの原則を理解した。さらに彼は、ストレージ選定は単なる製品比較ではなく、ユースケース・<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>・予算・チームスキルを総合的に判断する必要があることを学んだ。数ヶ月後、彼はチームを説得して<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>ラボを本格運用に移行し、NASの定期的な容量不足ミーティングは完全に撲滅されたのだった。）
