---
layout: post
title: "NVMe over RDMA ― RoCEv2とInfiniBandで実現する超低レイテンシストレージ"
date: 2026-06-19 09:00:00 +0900
tags: [storage, nvme, rdma, roce, infiniband]
description: "RDMAの基本からInfiniBand・RoCEv2・iWARPの比較、NVMe over RDMAの実測性能、PFC/DCQCN設計、GPUDirect RDMAまで徹底解説。"
---

お盆休み明けの火曜日。新人君がデータセンタのサーバルームで、<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>の性能測定結果を前に首をかしげている。計測値はカタログスペックの3割も出ていない。

「先輩、この<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>、カタログではランダム読込み100万IOPSって書いてあるのに、ネットワーク越しだと30万IOPSしか出てないんですけど…」

『ああ、それ<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>のオーバーヘッドだな。LinuxのTCP/IPスタックを通すと、割と性能が落ちる。もっとレイテンシを詰めたいなら<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の世界に行くことになる。』

「<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>…前に<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>の時にも話に出ましたよね。<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>を介さずにNICが直接メモリにアクセスする方式」

『そう。<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>はRemote Direct Memory Accessの略だ。一言で言えば「<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>に割り込みをかけずに、NICが直接アプリケーションのメモリ領域にデータを置く」。これを<ruby>ゼロコピー<rp>《</rp><rt>ゼロコピー</rt><rp>》</rp></ruby>と<ruby>カーネルバイパス<rp>《</rp><rt>カーネルバイパス</rt><rp>》</rp></ruby>と呼ぶ。』

「<ruby>ゼロコピー<rp>《</rp><rt>ゼロコピー</rt><rp>》</rp></ruby>と<ruby>カーネルバイパス<rp>《</rp><rt>カーネルバイパス</rt><rp>》</rp></ruby>…聞いたことはあるけど、具体的に何が嬉しいんですか？」

『通常のTCP通信では、データはこう流れる。NIC→カーネルバッファ→アプリバッファ、と2回コピーされる。さらにシステムコールのオーバーヘッド、コンテキストスイッチも発生する。<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>ならNICが直接アプリのメモリにDMAする。コピー回数がゼロで、カーネルを経由しない。結果、レイテンシが1桁下がるし<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>使用率も激減する。』

「なるほど…で、<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>にも種類があるって聞きました。<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>と<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>と<ruby>iWARP<rp>《</rp><rt>アイワープ</rt><rp>》</rp></ruby>の3つですよね？」

『よく調べてきたな。そうだ、大きく分けて3方式ある。まず<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>。これは<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>専用に作られたネットワークで、最も低レイテンシ。ただし専用のケーブルとスイッチが必要で、コストが高い。』

「専用網ってことは、イーサネットとは完全に別の世界ってことですか？」

『そう。<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>は独自のプロトコルスタックを持ってて、<ruby>Subnet Manager<rp>《</rp><rt>サブネットマネージャ</rt><rp>》</rp></ruby>がトポロジを管理する。各エンドポイントにはLID（Local Identifier）が割り当てられて、LIDベースのルーティングが行われる。<ruby>ロスレス<rp>《</rp><rt>ロスレス</rt><rp>》</rp></ruby>なファブリックが標準で、<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>のための完全なエコシステムができてる。』

「<ruby>Subnet Manager<rp>《</rp><rt>サブネットマネージャ</rt><rp>》</rp></ruby>って、<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>のネットワークを管理するコントローラみたいなものですか？」

『そうだ。SMがLIDの割り当て、経路計算、障害時の経路再計算を全て担当する。冗長構成も可能で、アクティブ/スタンバイで動かす。これがないと<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>は動かない。』

「ふーん…で、二つ目が<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>ですね。前に<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>って話が出ましたけど、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>はどう違うんですか？」

『<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>は<ruby>RDMA over Converged Ethernet<rp>《</rp><rt>アールディーエムエーオーバーコンバージドイーサネット</rt><rp>》</rp></ruby>の略だ。v1はイーサネットの<ruby>L2<rp>《</rp><rt>エルツー</rt><rp>》</rp></ruby>だけで動いたが、v2はUDP/IP上で動く。つまり既存のIPネットワークに<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>を乗せられる。これが革命だった。普通のイーサネットスイッチで<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>が使える。』

「それってすごくないですか？専用網いらずで超低レイテンシが手に入るってことですよね？」

『理論上はそうだ。ただし、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>は「ベストエフォートのイーサネットの上に<ruby>ロスレス<rp>《</rp><rt>ロスレス</rt><rp>》</rp></ruby>を要求する<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>を無理やり載せた」というのが実態だ。だからPFC（Priority Flow Control）でリンクレベルを<ruby>ロスレス<rp>《</rp><rt>ロスレス</rt><rp>》</rp></ruby>に変換して、ECN＋<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>で輻輳を制御する。』

「またPFCと<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>の話が出てきましたね。先週の<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>の時と同じやつだ」

『そう。<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>が動作するネットワークは、PFCでクラス単位の<ruby>ロスレス<rp>《</rp><rt>ロスレス</rt><rp>》</rp></ruby>保証をして、<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>でエンドツーエンドの輻輳制御をする。ただし、この組み合わせが非常にデリケートで、パラメータチューニングを間違えると<ruby>PFCデッドロック<rp>《</rp><rt>ピーエフシーデッドロック</rt><rp>》</rp></ruby>やストームが発生する。』

「それが<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>の最大の課題ってやつですね。三つ目の<ruby>iWARP<rp>《</rp><rt>アイワープ</rt><rp>》</rp></ruby>はどうなんですか？」

『<ruby>iWARP<rp>《</rp><rt>アイワープ</rt><rp>》</rp></ruby>は<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>をTCPの上で実装した方式だ。TCPの持つ信頼性と輻輳制御をそのまま使うから、PFCのような特殊な設定が不要だ。互換性は最も高い。ただし、TCPのオーバーヘッドがあるから、<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>や<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>ほどの低レイテンシは出ない。』

「結局どれが一番いいんですか？」

『トレードオフだ。<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>は最高性能だが高コスト、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>はコストパフォーマンスが高いが設定が難しい、<ruby>iWARP<rp>《</rp><rt>アイワープ</rt><rp>》</rp></ruby>は互換性重視だが性能は中間。選択は要件次第だ。とはいえ、ストレージ業界の主流は<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>だ。特に<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>という形で爆発的に普及してる。』

「<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>って、<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>と何が違うんですか？」

『<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>は<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>コマンドをTCPセグメントに載せる。<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>は<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>のSend/Write/Readオペレーションで直接転送する。実測値で比較すると、レイテンシは<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>が5〜15<ruby>マイクロ秒<rp>《</rp><rt>マイクロビョウ</rt><rp>》</rp></ruby>、<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>が20〜60<ruby>マイクロ秒<rp>《</rp><rt>マイクロビョウ</rt><rp>》</rp></ruby>。<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>使用率も<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の方が圧倒的に低い。』

「5<ruby>マイクロ秒<rp>《</rp><rt>マイクロビョウ</rt><rp>》</rp></ruby>…つまりTCPの4分の1以下ってことですか？」

『そう。特に4Kランダム読込みのレイテンシが劇的に違う。例えば、<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>で5マイクロ秒程度のレイテンシが、<ruby>NVMe over TCP<rp>《</rp><rt>エヌブイエムイーオーバーティーシーピー</rt><rp>》</rp></ruby>だと50マイクロ秒近くになることもある。この差はデータベースのOLAP処理やAIの分散学習で顕著に出る。』

「でも<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>ってNICにも依存しますよね？対応NICが必要だし…」

『もちろん。最近のNICは大抵<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>に対応してる。Mellanox（今のNVIDIA）のConnectXシリーズはもちろん、<ruby>Broadcom<rp>《</rp><rt>ブロードコム</rt><rp>》</rp></ruby>、<ruby>Intel<rp>《</rp><rt>インテル</rt><rp>》</rp></ruby>のNICも対応してきてる。Linuxではmlx5_coreドライバが標準で<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>をサポートしてる。』

「じゃあ実際に使うには、どういう設定が必要なんですか？」

『まずNICの<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>対応を有効にする。次にPFCの設定。スイッチ側で<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のトラフィッククラスに優先度を割り当てて、PFCを有効にする。最後に<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>のチューニング。これでようやく使える。』

「結構手順が多いですね…」

『その上でさらに問題がある。<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のPFC依存設計には既知のリスクがある。代表的なのは<ruby>PFCデッドロック<rp>《</rp><rt>ピーエフシーデッドロック</rt><rp>》</rp></ruby>、ホットスポット輻輳、そしてPFCストームだ。』

「<ruby>PFCデッドロック<rp>《</rp><rt>ピーエフシーデッドロック</rt><rp>》</rp></ruby>って、複数スイッチ間でPFCが連鎖して全停止するやつですよね。先週も出ました」

『そう。ホットスポットは特定のリンクにトラフィックが集中して、バッファが溢れてPFCが発動し、周辺全部の通信が止まる。PFCストームはPFCフレームが制御不能に連鎖する現象だ。いずれも、<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の性能を一気にゼロ近くまで落とす。』

「それってどうやって回避するんですか？」

『最近のトレンドは<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>の高度化と、スイッチ側のバッファ設計の改善だ。特にNVIDIAのSpectrumスイッチとか、<ruby>Broadcom<rp>《</rp><rt>ブロードコム</rt><rp>》</rp></ruby>のJerichoシリーズは大量のバッファを搭載して、PFCストームを吸収できる。さらに、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のトラフィックを専用の<ruby>VLAN<rp>《</rp><rt>ブイラン</rt><rp>》</rp></ruby>に分離して、他のトラフィックとPFCドメインを分ける設計が推奨されてる。』

「なるほど…物理的に分離するのが一番確実なんですね。ところで先輩、最近AI関連で<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>って言葉をよく見かけるんですけど、あれって何ですか？」

『<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>はNVIDIAが開発した技術で、GPUのメモリにNICが直接DMAできる。通常は<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>のメインメモリを経由する必要があるが、<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>なら<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>を通さずに、NIC→GPUメモリの直接パスが開かれる。』

「えっ、それってGPUが直接ネットワークからデータを受け取れるってこと？」

『そうだ。AIの分散学習では、複数のGPU間で勾配データを転送する必要がある。通常はGPUメモリ→<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>メモリ→NIC→ネットワーク→相手NIC→<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>メモリ→相手GPUメモリ、という経路になる。<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>ならNIC→相手GPUメモリに直接届く。レイテンシで言うと、従来比で半分以下になる。』

「それは大きいですね…AI学習では勾配同期が律速になりがちだから」

『その通り。特に大規模言語モデルの学習では、数百台のGPUが同期して勾配を交換する。この時のAllReduce通信に<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>を使うと、学習時間が劇的に短縮される。NVIDIAのDGXシステムやH100のNVLink+<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>構成は、この思想で設計されてる。』

「じゃあAI基盤には<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>＋<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>がベストってことですか？」

『今のところはな。ただ、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>でも<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>は使える。NVIDIAのConnectX-7以降は<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>でも<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>をフルサポートしてる。だからコスト重視なら<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>、最高性能重視なら<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>って住み分けになってる。』

「なるほど…ということは、データセンタ内で両方を使い分けるケースもあるんですね。AIクラスタは<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>、それ以外のストレージは<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>みたいな」

『よくわかってるじゃないか。実際の大規模データセンタでは、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>/AIクラスタに<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>、汎用コンピューティング＋ストレージに<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>、というハイブリッド構成が増えてる。両方とも<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>で繋ぐことで、データの移動レイテンシを最小化できる。』

「でも待ってください。<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>と<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>ってプロトコルが違うのに、どうやって同じストレージにアクセスするんですか？」

『そこは<ruby>NVMe-oF<rp>《</rp><rt>エヌブイエムイーオーヴァーファブリックス</rt><rp>》</rp></ruby>の抽象化が効いてる。<ruby>NVMe-oF<rp>《</rp><rt>エヌブイエムイーオーヴァーファブリックス</rt><rp>》</rp></ruby>はトランスポート層を抽象化してるから、イニシエータ側は「<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>」でも「<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>」でも、同じ名前空間にアクセスできる。ターゲット側で両方のトランスポートを同時に公開することも可能だ。』

「<ruby>NVMe-oF<rp>《</rp><rt>エヌブイエムイーオーヴァーファブリックス</rt><rp>》</rp></ruby>のトランスポート抽象化、前にも教わりましたけど、ここで効いてくるんですね」

『そう。理論上は<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>と<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>の両方を一つの<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>サブシステムでサポートできる。ただし、実際の製品では<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>はトランスポートとして統合されてないケースも多いから、ベンダの仕様を確認する必要がある。』

「先輩、今日はいろいろありがとうございました。おかげで<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の全体像が掴めました」

『最後にもう一つだけ。<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の世界では「レイテンシは語るものではなく、測るものだ」って格言がある。カタログスペックじゃなくて、自分の環境で実測しろって意味だ。<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のPFCカウンタや<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>のパラメータは、実測しながら詰めるのが一番確実だ。』

「わかりました。週末にConnectX-6のNICを2台買って、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のラボを組んでみます！」

『…おい、それなりの出費になるぞ。でも背中を押すなら、その経験は絶対に後悔しない。<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の設計ができるエンジニアはまだまだ少ないからな。』

（週末、新人君は中古のConnectX-6を2台と25Gbpsのスイッチを1台、ヤフオクで落札していた。そして日曜の夜、無事に<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のリンクが確立。PFCカウンタを監視しながら、<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby> over <ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>で実測100万IOPSを達成した瞬間、彼は静かにガッツポーズをした。その隣では、<ruby>GPUDirect RDMA<rp>《</rp><rt>ジーピーユーダイレクトアールディーエムエー</rt><rp>》</rp></ruby>の資料がTabで開かれていた。）
