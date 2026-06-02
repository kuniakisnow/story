---
layout: post
title: "CXL Type-3メモリデバイスの実力 ― Samsung・SK hynix・Micronの最新製品"
date: 2026-06-06 09:00:00 +0900
tags: [cxl, type3, memory]
description: "CXL Type-3メモリデバイスのアーキテクチャ、Samsung CMM-D・SK hynix NGD・Micron CZ120の実製品比較、Linuxホスト対応、NUMAエクステンダとしての活用を解説する"
---

金曜の午後。新人君がニュースサイトで見つけた記事を手に、先輩のデスクへ駆け寄る。

「先輩！ <ruby>PCIe<rp>《</rp><rt>ピーシーアイイー</rt><rp>》</rp></ruby>スロットに挿す<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>モジュールって本当にあるんですか？ <ruby>Samsung<rp>《</rp><rt>サムスン</rt><rp>》</rp></ruby>とかSK hynixとかが出してるって書いてあるんですけど、これって何なんですかね？」

先輩がモニターから顔を上げる。

『お、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Type-3メモリデバイスの話だな。あるある。ちゃんと買える製品がもう出てるんだ。<ruby>Samsung<rp>《</rp><rt>サムスン</rt><rp>》</rp></ruby>の<ruby>CMM-D<rp>《</rp><rt>シーエムエムディー</rt><rp>》</rp></ruby>、SK hynixの<ruby>NGD<rp>《</rp><rt>エヌジーディー</rt><rp>》</rp></ruby>、<ruby>Micron<rp>《</rp><rt>マイクロン</rt><rp>》</rp></ruby>の<ruby>CZ120<rp>《</rp><rt>シージー120</rt><rp>》</rp></ruby>——<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>三大メーカーが本気で投入してる』

「<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>ってCompute Express Linkですよね。<ruby>PCIe<rp>《</rp><rt>ピーシーアイイー</rt><rp>》</rp></ruby>の上で動くキャッシュコヒーレントなインターコネクト…だった気がします」

『お、よく予習してるな。<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>にはType-1、Type-2、Type-3の3種類がある。Type-1はキャッシュ機能付きアクセラレータで<ruby>CXL.io<rp>《</rp><rt>シーエックスエルアイオー</rt><rp>》</rp></ruby>と<ruby>CXL.cache<rp>《</rp><rt>シーエックスエルキャッシュ</rt><rp>》</rp></ruby>をサポート。Type-2はメモリ内蔵アクセラレータで全プロトコル対応——GPUや<ruby>FPGA<rp>《</rp><rt>エフピージーエー</rt><rp>》</rp></ruby>がこれに当たる。そしてType-3がメモリバッファ専用で、<ruby>CXL.io<rp>《</rp><rt>シーエックスエルアイオー</rt><rp>》</rp></ruby>と<ruby>CXL.mem<rp>《</rp><rt>シーエックスエルメム</rt><rp>》</rp></ruby>をサポートする。要は<ruby>PCIe<rp>《</rp><rt>ピーシーアイイー</rt><rp>》</rp></ruby>スロットに挿す<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>モジュールだと思っていい』

「Type-3はメモリ専用なんですね。具体的な製品を教えてください」

『<ruby>Samsung<rp>《</rp><rt>サムスン</rt><rp>》</rp></ruby>の<ruby>CMM-D<rp>《</rp><rt>シーエムエムディー</rt><rp>》</rp></ruby>——<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Memory Module <ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>-based——は128〜512GBのラインアップで、<ruby>PCIe Gen5<rp>《</rp><rt>ピーシーアイイージェネレーションファイブ</rt><rp>》</rp></ruby> x8接続。特徴はメモリプーリング機能で、複数ホストで共有できる。これによりサーバ単位でメモリが余っても、他のサーバに融通できるようになる』

「複数ホストで共有？！ 一つのメモリを複数のサーバで同時に読めるってことですか？」

『そこは誤解しやすいが、正確には「論理分割」だ。物理的には一つのデバイスでも、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>スイッチ経由で複数のホストに異なるアドレス範囲を割り当てる。メモリプーリング——リソースをプールして必要に応じて分配する——という概念だ。データセンター全体でのメモリ使用率が上がるから、大規模運用では大きなメリットになる』

「SK hynixのはどうですか？」

『SK hynixの<ruby>NGD<rp>《</rp><rt>エヌジーディー</rt><rp>》</rp></ruby>——Next Generation <ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>——は<ruby>HBM<rp>《</rp><rt>エイチビーエム</rt><rp>》</rp></ruby>技術を応用している。<ruby>HBM<rp>《</rp><rt>エイチビーエム</rt><rp>》</rp></ruby>はGPUに使われる広帯域メモリで、TSV（シリコン貫通電極）で<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>チップを積層する技術だ。それを<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Type-3に応用することで、なんと最大1TBを実現している。ECC内蔵でRAS機能も高い』

「1TB？！ サーバのメインメモリが一気に倍にできそうですね」

『しかも<ruby>PCIe<rp>《</rp><rt>ピーシーアイイー</rt><rp>》</rp></ruby>スロット1本で増設できる。サーバのメモリスロットに空きがなくても、<ruby>PCIe<rp>《</rp><rt>ピーシーアイイー</rt><rp>》</rp></ruby>スロットがあれば拡張できる——これは<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>の自由度が大きく変わる。<ruby>Micron<rp>《</rp><rt>マイクロン</rt><rp>》</rp></ruby>の<ruby>CZ120<rp>《</rp><rt>シージー120</rt><rp>》</rp></ruby>は最大256GBだが、独自の1β（1-beta）プロセスにより消費電力を競合比15%削減している。同じ256GBでも、消費電力が低ければラック全体の冷却負荷が減るから、データセンターにとっては大きなアドバンテージだ』

「どのくらい速いんですか？ 普通の<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>と同じ感覚で使えるんですか？」

『そこがミソだ。<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>比で2〜5倍のレイテンシ——つまり遅い。<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>が80〜100<ruby>ナノ秒<rp>《</rp><rt>ナノビョウ</rt><rp>》</rp></ruby>なのに対し、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Type-3は200〜500<ruby>ナノ秒<rp>《</rp><rt>ナノビョウ</rt><rp>》</rp></ruby>といったところだ。とはいえ<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>の数十<ruby>マイクロ秒<rp>《</rp><rt>マイクロビョウ</rt><rp>》</rp></ruby>と比べれば圧倒的に速い。<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>とストレージの間に新しいメモリ階層を作る——まさにそのための製品群だ』

「<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>の10倍近く遅いけど、SSDの100倍は速い…中途半端にも見えますけど、その中間が欲しかったんですね」

『その通り。これまでは「速いけど容量が小さい<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>」か「遅いけど容量が大きいSSD」の二択しかなかった。<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Type-3は「そこそこの速度で大容量」という第三の選択肢を提供する。これはメモリ階層における新たな層——<ruby>Tier 2<rp>《</rp><rt>ティアツー</rt><rp>》</rp></ruby>メモリ——の誕生だ』

「<ruby>Intel<rp>《</rp><rt>インテル</rt><rp>》</rp></ruby> Optaneが消えた後の穴を埋める感じですか？」

『良い観点だ。Optaneは<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに容量と速度のギャップを埋める存在だったが、製造コストが高くて撤退した。<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby> Type-3は同じギャップを埋めるが、既存の<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>技術をそのまま使えるためコスト面でも入手性でも有利だ。容量の拡張性ではむしろ<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>の方が上回る』

「実際に使うにはLinux側の準備も必要ですよね？」

『カーネル5.12以降で<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>の基本サポートが入っている。管理ツールは<ruby>daxctl<rp>《</rp><rt>ダックスクティーエル</rt><rp>》</rp></ruby>と<ruby>ndctl<rp>《</rp><rt>エヌディークティーエル</rt><rp>》</rp></ruby>だ。<ruby>daxctl<rp>《</rp><rt>ダックスクティーエル</rt><rp>》</rp></ruby>で<ruby>DAX<rp>《</rp><rt>ダックス</rt><rp>》</rp></ruby>デバイスとして公開すれば、アプリケーションが直接メモリアクセスできる——いわゆるロードストアアクセスが可能になる。ファイルシステムのページキャッシュを経由せずに、デバイス上のメモリに直接Read/Writeできるんだ』

「メモリマップドI/Oのように扱えるわけですね」

『そう。もう一つの使い方が<ruby>kmem<rp>《</rp><rt>ケイメム</rt><rp>》</rp></ruby>ドライバ。これを使えば<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリを通常のシステムメモリとして認識させられる。その場合、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリは新しい<ruby>NUMA<rp>《</rp><rt>ヌーマ</rt><rp>》</rp></ruby>ノードとして追加される』

「<ruby>NUMA<rp>《</rp><rt>ヌーマ</rt><rp>》</rp></ruby>って<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>から遠いメモリのことですよね」

『そう。<ruby>NUMA<rp>《</rp><rt>ヌーマ</rt><rp>》</rp></ruby>には距離の概念があって、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリはリモート<ruby>NUMA<rp>《</rp><rt>ヌーマ</rt><rp>》</rp></ruby>ノードとして認識される。つまり「ちょっと遠いメモリ」としてOSが自動管理する。これが実は絶妙な設計で、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリを<ruby>NUMA<rp>《</rp><rt>ヌーマ</rt><rp>》</rp></ruby>エクステンダとして使うのが最も実用的な<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>になる』

「ローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>より遅いことを前提に、使い分けるわけですね」

『そういうこと。ホットデータはローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>、コールドデータは<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリ——この階層化構成が王道だ。Linuxの<ruby>Auto NUMA Balancing<rp>《</rp><rt>オートヌーマバランシング</rt><rp>》</rp></ruby>を使えば、アクセス頻度に応じて自動的に<ruby>ページ<rp>《</rp><rt>ページ</rt><rp>》</rp></ruby>を昇格させられる。アクセスが集中している<ruby>ページ<rp>《</rp><rt>ページ</rt><rp>》</rp></ruby>を<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>からローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>に移す。この仕組みを「メモリティアリング」と呼ぶ』

「まるで<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>のキャッシュ階層みたいですね。<ruby>L1<rp>《</rp><rt>エルワン</rt><rp>》</rp></ruby>/<ruby>L2<rp>《</rp><rt>エルツー</rt><rp>》</rp></ruby>/<ruby>L3<rp>《</rp><rt>エルスリー</rt><rp>》</rp></ruby>キャッシュ、ローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリ…5階層か」

『面白い捉え方だ。さらに<ruby>CXL 2.0<rp>《</rp><rt>シーエックスエルにいてんぜろ</rt><rp>》</rp></ruby>ではスイッチ経由のマルチホストファブリックが標準化されている。スイッチを使えば、ラック内の複数ホスト間でメモリプールを動的に再配分できる。例えばあるサーバでメモリ需要が急増したら、他のサーバに割り当てていた<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリを即座に引きはがして再割り当てできる』

「動的に変えられる？！ それって従来の物理メモリ増設とは根本的に違いますね」

『その通り。メモリの<ruby>アロケーション<rp>《</rp><rt>アロケーション</rt><rp>》</rp></ruby>がソフトウェアで柔軟に変えられる。サーバの電源を落とさずにメモリ容量を増やせる——これは従来のサーバ設計とは根本的に異なる<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>モデルだ。もちろんパフォーマンスの分離や<ruby>QoS<rp>《</rp><rt>キューオーエス</rt><rp>》</rp></ruby>の課題はあるが、それを含めて研究が進んでいる』

「でも複数ホストで共有するとなると、セキュリティとかリソースの分離はどうなるんですか？」

『<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>のメモリプーリングでは、デバイス自体が各ホストに割り当てられたアドレス範囲をハードウェアレベルで隔離する。あるホストが別のホストのメモリ領域にアクセスすることは物理的にできない。また<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>スイッチには<ruby>ACS<rp>《</rp><rt>エーシーエス</rt><rp>》</rp></ruby>（Access Control Service）相当の機能が備わっていて、バスレベルでのアクセス制御も可能だ』

「なるほど…ハードで守ってるわけですね」

『そう。<ruby>CXL 3.0<rp>《</rp><rt>シーエックスエルさんてんぜろ</rt><rp>》</rp></ruby>ではさらに、マルチレベルスイッチングやファブリック管理の标准規格が拡充されている。ラック単位、さらにはラック間をまたぐメモリプールも視野に入っている』

「データセンター全体が一つの大きなメモリプールに…SFみたいですね」

『実際、<ruby>Meta<rp>《</rp><rt>メタ</rt><rp>》</rp></ruby>やGoogle(グーグル)は<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>対応サーバの大規模導入を表明している。今後2〜3年でデータセンターの標準構成になる可能性が高い』

「データセンターの設計が大きく変わりそうですね」

『<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>対応<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>——<ruby>Intel<rp>《</rp><rt>インテル</rt><rp>》</rp></ruby>のXeon（Granite RapidsやDiamond Rapids）、<ruby>AMD<rp>《</rp><rt>エーエムディー</rt><rp>》</rp></ruby>のEPYC（Turin以降）、Ampere等——が本格普及すれば、サーバのメモリ容量を柔軟に拡張できる標準構成になるだろう。<ruby>LLM<rp>《</rp><rt>エルエルエム</rt><rp>》</rp></ruby>の推論やインメモリ<ruby>DB<rp>《</rp><rt>データベース</rt><rp>》</rp></ruby>、リアルタイム分析の需要が増える中で、この「中間メモリ層」の立ち位置はますます重要になる。特に<ruby>LLM<rp>《</rp><rt>エルエルエム</rt><rp>》</rp></ruby>の推論では、モデルの重みを<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリに載せておいて、必要な分だけローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>に呼び込むという<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>が有効だ』

「先輩、ちょっといいですか？ この階層化メモリの概念図を描いてみたんですけど、見てもらえます？」

新人君がホワイトボードに描いたのは、<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>を頂点に、<ruby>L1<rp>《</rp><rt>エルワン</rt><rp>》</rp></ruby>/<ruby>L2<rp>《</rp><rt>エルツー</rt><rp>》</rp></ruby>/<ruby>L3<rp>《</rp><rt>エルスリー</rt><rp>》</rp></ruby>キャッシュ、ローカル<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリ、<ruby>NVMe SSD<rp>《</rp><rt>エヌブイエムイーエスエスディー</rt><rp>》</rp></ruby>の5層が階層をなす構成図だった。それぞれの層にレイテンシと容量が赤字で書き込まれている。

『お、なかなかいいじゃないか。でも<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>の容量がちょっと小さいな。1TB超えもあり得るから、もっと大きく書いていいぞ』

「じゃあこうですか？」

新人君が<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>メモリの層を倍の大きさに書き直す。先輩が満足そうにうなずいた。

『よし、それなら実運用のイメージが湧くな。その図、社内のWikiに貼っておけ。新人研修の教材にも使える』

「はい！ ありがとうございます！」

新人君はホワイトボードの前に立ち、自分で描いたメモリ階層図を見つめながら、メモリとストレージの境界が溶けていく未来に胸を膨らませていた。かつて「近いけど小さい<ruby>DRAM<rp>《</rp><rt>ディーラム</rt><rp>》</rp></ruby>」と「遅いけど大きいストレージ」の二択だった世界に、<ruby>CXL<rp>《</rp><rt>シーエックスエル</rt><rp>》</rp></ruby>は「その中間」という新しい選択肢をもたらした。それがサーバアーキテクチャの常識を根本から書き換えようとしている——そのうねりを感じた金曜の午後だった。
