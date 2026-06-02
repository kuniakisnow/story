---
layout: post
title: "データセンタネットワークトポロジ ― Spine-Leaf／Dragonfly／Fat-Tree"
date: 2026-08-10 09:00:00 +0900
tags: [network, datacenter, topology, spine-leaf]
description: "データセンタネットワークのトポロジ設計をSpine-Leaf、Dragonfly、Fat-Treeの3つに焦点を当てて解説。VXLAN/EVPNオーバレイやRoCEv2対応の設計まで。"
---

台風が近づく蒸し暑い火曜日。新人君がデータセンタのネットワーク構成図を前に頭を抱えている。モニタには、複雑に絡み合った3層構成の配線図が映し出されていた。

「先輩、このネットワーク構成、なんか変じゃないですか？CoreスイッチとAggregationスイッチの間のリンク、全部使い切ってるのに、サーバ側の帯域が全然足りてないんですけど…」

『お、いいところに気づいたな。それ、従来の3層構成（Core/Aggregation/Access）の限界ってやつだ。』

「3層構成って、昔からあるスタンダードなやつですよね？何が問題なんですか？」

『問題は主に2つ。帯域の輻輳と<ruby>East-West<rp>《</rp><rt>イーストウエスト</rt><rp>》</rp></ruby>トラフィックの増大だ。昔のアプリケーションはクライアント→サーバの<ruby>North-South<rp>《</rp><rt>ノースサウス</rt><rp>》</rp></ruby>トラフィックがほとんどだった。でも今は違う。VMのマイグレーション、分散ストレージのデータ同期、AI学習のシャッフル通信…全部が<ruby>East-West<rp>《</rp><rt>イーストウエスト</rt><rp>》</rp></ruby>、つまりサーバ間の通信だ。』

「<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のデータ同期とか、Sparkのシャッフルとか、全部サーバ間でめっちゃ帯域使いますね」

『3層構成はこの<ruby>East-West<rp>《</rp><rt>イーストウエスト</rt><rp>》</rp></ruby>トラフィックに弱い。Aggregationスイッチを経由するたびに帯域が絞られる。例えばAccessスイッチのアップリンクが40Gbpsなのに、AggregationからCoreへのリンクが10Gbpsしかなかったりする。これがオーバーサブスクリプションだ。』

「<ruby>Over-subscription比<rp>《</rp><rt>オーバーサブスクリプションひ</rt><rp>》</rp></ruby>ってやつですね。設計によって変わると」

『そう。そんな中で登場したのが<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>トポロジだ。一言で言えば「全Leafスイッチが全Spineスイッチに接続する」という究極のメッシュ<ruby>結合<rp>《</rp><rt>けつごう</rt><rp>》</rp></ruby>だ。』

「え？Leafが全部、全部のSpineに繋がるんですか？それって配線がめちゃくちゃ多くないですか？」

『その代わり、どんな通信でもホップ数が固定の2で済む。Leaf→Spine→Leafの2ホップだ。3層構成のようにAggregationで詰まることがない。Leafを増やすだけで帯域が線形に拡張できる。』

「帯域が線形に拡張…それってスケールアウトの考え方そのものですね」

『そして<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>の要となる技術が<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>だ。Equal-Cost Multi-Path、日本語では等コストマルチパス。Spineに複数の経路があっても、同じコストなら全部使って分散できる。』

「<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>って、<ruby>L3<rp>《</rp><rt>エルスリー</rt><rp>》</rp></ruby>のハッシュベースのロードバランシングですよね。でもそれってハッシュの衝突で偏ったりしません？」

『いい指摘だ。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>では全Leafが全Spineに繋がってるから、<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>のハッシュ空間が広い。フロー数が多ければ多いほど統計的に均等に分散される。ただし、一つのフロー（TCPコネクション）は必ず同じ経路を通るから、フロー単位の順序性は保たれる。』

「なるほど…それで、さっき出た<ruby>Over-subscription比<rp>《</rp><rt>オーバーサブスクリプションひ</rt><rp>》</rp></ruby>の設計はどう考えるんですか？」

『<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>でも<ruby>Over-subscription比<rp>《</rp><rt>オーバーサブスクリプションひ</rt><rp>》</rp></ruby>は設計項目だ。例えばLeafスイッチのダウンリンク（サーバ側）が合計480Gbps（25Gbps×16ポート＋α）で、アップリンク（Spine側）が400Gbps（100Gbps×4）なら、480÷400で1.2:1。もちろん1:1、つまり完全なノンブロッキング構成も可能だ。その場合はSpineへのリンクを増やす。』

「じゃあ3:1とか4:1ってのは、アップリンクを意図的に絞ってコストを下げてるってことですね」

『そう。多くのデータセンタでは3:1や4:1で設計してる。全部をノンブロッキングにするコストはバカにならない。どの程度のオーバーサブスクリプションまで許容できるかは、ワークロード次第だ。ところで、<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>よりさらに先進的なトポロジがあるのを知ってるか？』

「え、<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>よりすごいのが？」

『<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>だ。これはエクサスケール<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>向けに開発されたトポロジで、直径がたった3ホップだ。』

「3ホップで済むんですか？どんな構造なんです？」

『<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>は「グループ」という単位で考える。グループ内のスイッチは全部互いに接続するフルメッシュ。そしてグループ間は少数のリンクで接続する。一つのグループを大きくすればするほど、グループ間のリンクが少なくて済む。スケーラビリティが極めて高い。』

「でもそれって、グループ間のリンクがボトルネックにならないですか？」

『そこが<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>の設計思想の肝だ。グループ間リンクは<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに少数だが、ルーティングを工夫して回避する。具体的にはALTO（Adaptive Load-aware dOmino）ルーティングとか、VAL（Virtual Airlane）ルーティングで、混雑を避けて動的に経路を変える。』

「なるほど…<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>と<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>、結局どっちを選べばいいんですか？」

『それはスケールと用途次第だ。DCネットワーク全体なら<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>が事実上の標準だ。でも数千台〜数万台のノードを繋ぐ<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタでは<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>が強みを発揮する。もう一つ、<ruby>Fat-Tree<rp>《</rp><rt>ファットツリー</rt><rp>》</rp></ruby>ってトポロジも知っておくといい。』

「<ruby>Fat-Tree<rp>《</rp><rt>ファットツリー</rt><rp>》</rp></ruby>って、木構造のツリーが太くなるやつですか？」

『そう。k-ary n-treeとも呼ばれて、<ruby>Clos<rp>《</rp><rt>クロス</rt><rp>》</rp></ruby>ネットワークの一種だ。バイセクション帯域（ネットワークを半分に切った時の帯域）が<ruby>Full<rp>《</rp><rt>フル</rt><rp>》</rp></ruby>になる設計にできる。完全なノンブロッキング構成を数学的に設計できるのが特徴だ。』

「<ruby>Clos<rp>《</rp><rt>クロス</rt><rp>》</rp></ruby>ネットワーク…電話交換機のアーキテクチャですよね？チャールズ・クロスが1950年代に発明した」

『よく知ってるな。<ruby>Clos<rp>《</rp><rt>クロス</rt><rp>》</rp></ruby>ネットワークは電話交換用に考案されたが、今のデータセンタネットワークの数学的基盤になってる。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>も<ruby>Fat-Tree<rp>《</rp><rt>ファットツリー</rt><rp>》</rp></ruby>も広義の<ruby>Clos<rp>《</rp><rt>クロス</rt><rp>》</rp></ruby>ネットワークだ。基本は「入力段→中間段→出力段」の3段構成で、これを多段に拡張することで大規模なノンブロッキング網を実現する。』

「じゃあ物理トポロジは<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>にして、その上で<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>でオーバレイを張るのが現代の標準って感じですか？」

『その通り。<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>で<ruby>L2<rp>《</rp><rt>エルツー</rt><rp>》</rp></ruby>ネットワークを論理的に拡張して、<ruby>EVPN<rp>《</rp><rt>イーブイピーエン</rt><rp>》</rp></ruby>でコントロールプレーンを統合する。<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>はUDPでカプセル化するから、既存のIPネットワークの上に論理的な<ruby>L2<rp>《</rp><rt>エルツー</rt><rp>》</rp></ruby>ネットワークを重ねられる。<ruby>EVPN<rp>《</rp><rt>イーブイピーエン</rt><rp>》</rp></ruby>はMP-BGPを使ってMACアドレスと<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>トンネルの対応を分散管理する。』

「<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>って、24ビットのVNIで約1600万の論理ネットワークを作れるやつですよね。従来の<ruby>VLAN<rp>《</rp><rt>ブイラン</rt><rp>》</rp></ruby>の4096をはるかに超える」

『そう。マルチテナント環境では必須の技術だ。さらに最近はマイクロセグメンテーションとゼロトラストの考え方も重要だ。ネットワークの境界をDCの外周だけでなく、サーバ間の通信一つ一つに適用する。』

「ゼロトラストって「信頼しない、常に検証する」でしたっけ？」

『そう。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>のフラットなトポロジは、実はゼロトラストと相性がいい。物理的なネットワークの構造に依存せず、論理的にセグメントを分割できるからだ。<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby>＋<ruby>EVPN<rp>《</rp><rt>イーブイピーエン</rt><rp>》</rp></ruby>でテナントごとに完全に分離されたオーバレイネットワークを構築して、テナント間の通信は一切許可しない。』

「でもそれだけだと<ruby>East-West<rp>《</rp><rt>イーストウエスト</rt><rp>》</rp></ruby>トラフィックのセキュリティは担保できないんじゃ？」

『そう。だから各サーバ内でファイアウォールポリシーを適用する。最近ではDPUやSmartNICにその機能をオフロードするケースも増えてる。例えば<ruby>NVIDIA BlueField<rp>《</rp><rt>エヌビディアブルーフィールド</rt><rp>》</rp></ruby>なら、ホスト<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>を通さずにDPUレベルでパケットフィルタリングができる。』

「DPUでセキュリティまでやるんですね。ところで先輩、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>対応ってどう考えるんですか？ストレージのトラフィックを<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>に乗せる時に気をつけることって」

『ああ、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>は<ruby>RDMA over Converged Ethernet<rp>《</rp><rt>アールディーエムエーオーバーコンバージドイーサネット</rt><rp>》</rp></ruby>の第2版だ。<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>を<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>上で動かすには、PFC（Priority Flow Control）とECN（Explicit Congestion Notification）と<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>（Data Center Quantized Congestion Notification）の3点セットが必須だ。』

「PFCはIEEE 802.1Qbbのリンクレベルのフロー制御ですよね。<ruby>ロスレス<rp>《</rp><rt>ロスレス</rt><rp>》</rp></ruby>な通信を実現するための」

『そう。<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>はUDP上で<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>を動かすから、パケットロスが起こると<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>の性能が劇的に落ちる。だからPFCでリンクレベルのロスを防ぐ。でもPFCにはデッドロックの問題がある。複数のスイッチでPFCが連鎖すると、ネットワーク全体が停止する。』

「<ruby>PFCデッドロック<rp>《</rp><rt>ピーエフシーデッドロック</rt><rp>》</rp></ruby>…聞いたことあります。あれってどう防ぐんですか？」

『対策としては、PFCのしきい値を適切に設定する、バッファサイズを十分に確保する、<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>の<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>で負荷を均等に分散する。さらに最近は<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>というエンドツーエンドの輻輳制御を使う。これはECNマークを検出した<ruby>受信側<rp>《</rp><rt>じゅしんがわ</rt><rp>》</rp></ruby>が送信側にレートを下げるよう通知する方式だ。』

「ECNはIPヘッダのフィールドを使ってキューイング遅延を通知するやつですね。<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>はそれを<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>に最適化したと」

『そう。<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>はECNマークの割合を元に、送信レートを動的に調整する。ただし、このチューニングが難しい。PFCのしきい値、ECNのマーキング確率、<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>のゲインパラメータ…全部が相互に影響し合う。』

「なるほど…机上の設計だけじゃなくて、実測とチューニングが必要ってことですね」

『そうだ。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>のトポロジは理論上きれいだが、実際に<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のトラフィックを流すと、想定外のホットスポットが発生する。特にincast（多対一の同時通信）が発生すると、PFC stormが起きてスループットが急降下する。』

「じゃあどうやって設計すればいいんですか？」

『まず、<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>用の専用<ruby>VLAN<rp>《</rp><rt>ブイラン</rt><rp>》</rp></ruby>か<ruby>VXLAN<rp>《</rp><rt>ブイエックスエラン</rt><rp>》</rp></ruby> VNIを分離する。PFCの影響範囲を限定するためだ。次に<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>の全リンクで<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>を有効にして負荷分散。さらに<ruby>DCQCN<rp>《</rp><rt>ディーシーキューシーエヌ</rt><rp>》</rp></ruby>のパラメータはベンダ推奨値から始めて、実測ベースで詰める。最後にバッファ設計。各スイッチのバッファ量を計算して、PFCストームを吸収できるか確認する。』

「結構泥臭い作業ですね…きれいな理論の裏に、実戦でのチューニングがあると」

『それがネットワークエンジニアリングの面白いところだ。さて、ここで一つクイズだ。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>トポロジの最大の弱点は何だと思う？』

「弱点…えっと、全部のLeafが全部のSpineに繋がるってことは、Spineが1台死んでも大丈夫だけど…Spine全体のバンド幅って上限がありますよね？」

『正解だ。<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>はLeafを増やせばLeaf間の帯域は増えるが、Spineそのものの処理能力が上限になる。Spineスイッチを増設すれば解決するが、その分コストは上がる。つまり、<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>は「水平方向には強いが、垂直方向のスケールにはコストがかかる」。これが<ruby>Dragonfly<rp>《</rp><rt>ドラゴンフライ</rt><rp>》</rp></ruby>や<ruby>Fat-Tree<rp>《</rp><rt>ファットツリー</rt><rp>》</rp></ruby>が研究され続ける理由だ。』

「なるほど…今度、自宅ラボで<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>を組んでみようかな。できればLeaf4台、Spine2台で」

『お、本格的だな。できたら<ruby>RoCEv2<rp>《</rp><rt>ローチェブイツー</rt><rp>》</rp></ruby>のトラフィックも流してみろ。PFCカウンタを監視して、どんなタイミングでpauseフレームが出るかを観察するといい。実はこれ、データセンタネットワークの設計者面接でよく聞かれる内容だぞ。』

「えっ、それ面接で出るんですか？！」

『ああ。俺も昔、<ruby>Spine-Leaf<rp>《</rp><rt>スパインリーフ</rt><rp>》</rp></ruby>のオーバーサブスクリプション比の計算を面接で聞かれて、汗かいた記憶がある。』

（その夜、新人君は帰宅後にラック図を描きながら、<ruby>ECMP<rp>《</rp><rt>イーシーエムピー</rt><rp>》</rp></ruby>のハッシュアルゴリズムと<ruby>PFCデッドロック<rp>《</rp><rt>ピーエフシーデッドロック</rt><rp>》</rp></ruby>のシミュレーションを始めた。気づけば午前3時。モニタには100台のLeafを模擬したネットワークシミュレータの結果が並んでいる。先輩が言う「実戦の泥臭さ」を、彼は自宅ラボで噛み締めていた。）
