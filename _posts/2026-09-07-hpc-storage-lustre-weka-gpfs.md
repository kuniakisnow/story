---
layout: post
title: "HPCストレージの世界 ― Lustre・GPFS・WEKA・BeeGFSを徹底比較"
date: 2026-09-07 09:00:00 +0900
tags: [storage, hpc, lustre, gpfs, parallel-fs]
description: "HPC向け並列ファイルシステムの主要4製品（Lustre・GPFS/Spectrum Scale・WEKA・BeeGFS）を徹底比較。アーキテクチャ、メタデータ管理、バーストバッファ、AI/HPCコンバージェンスまで解説。"
---

九月最初の月曜日、新人君がサーバルームのホワイトボードに「100GB/s超」「クライアント数10000」「レイテンシ100μs未満」と書いては消し、首をかしげながら先輩のデスクにプリントアウトした資料の束を抱えてやってきた。資料の表紙には「<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby> File System Overview」と書かれている。

「先輩！スーパーコンピュータのストレージって、帯域が100GB/sとか平気で超えてるんですけど！これ、うちのNASの1000倍以上じゃないですか。しかもクライアント数が数万とか書いてあるんですけど！」

『お、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージに興味を持ったか。今日はそのへんをじっくり教えてやる。まず、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の世界では「普通のストレージ」の常識が全く通用しない。そもそも<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>って何だか分かるか？』

「計算機シミュレーションとか、天気予報とか、ゲノム解析みたいな超大規模な計算をするコンピュータのことですよね」

『おお、いい線いってる。<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>はHigh Performance Computingの略で、簡単に言うと「普通のコンピュータでは解けない規模の問題を、多数の計算ノードを並列に使って解く」ための技術だ。そしてそのストレージには、普通のストレージとは全く異なる要件が課せられる。』

「普通のストレージと何が違うんですか？」

『三つの大きな違いがある。一つ目は並列アクセスだ。数千から数万のクライアント（計算ノード）が同時に同じファイルシステムにアクセスする。普通のNASでは同時接続数が数百程度が限界だが、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ではそれが桁違いだ。二つ目は大帯域。数百<ruby>GB<rp>《</rp><rt>ギガバイト</rt><rp>》</rp></ruby>/sから、最近のトップクラスだと数<ruby>TB<rp>《</rp><rt>テラバイト</rt><rp>》</rp></ruby>/sが当たり前だ。三つ目はメタデータ分離。ファイルの実データと、その在り処を示すメタデータを別々のサーバ群で管理する。』

「メタデータ分離…それってどういうことですか？」

『普通のNASでは一つの筐体の中でデータとメタデータを一緒に扱う。しかし、ファイルの作成、削除、属性変更といったメタデータ操作は、実はデータの読み書きよりずっと<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>負荷が高い。特に1バイトのファイルを作るのに、数百バイトのメタデータを書き込む必要がある。<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>のようにクライアントが数千もいると、このメタデータ操作だけでサーバの<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>が飽和してしまう。』

「だからメタデータ専用のサーバを立てて、データの読み書きとは完全に分離するんですね」

『その通り。このアプローチを最初に製品化したのが<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>だ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は1999年のプロジェクト開始から20年以上にわたって<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージのデファクトスタンダードとして君臨し続けている。』

「<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>…聞いたことあります！スパコンでよく使われてるって」

『そう。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はオープンソースの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>で、Top500に入るスパコンの過半数が採用している。基本アーキテクチャは大きく分けて三つのコンポーネントで構成される。』

「三つ？」

『<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>と<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>とクライアントだ。<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>はMetaData Server、つまりメタデータを管理するサーバだ。<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>は<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>と呼ばれる専用のストレージデバイスを持っていて、ファイル名、ディレクトリ構造、パーミッション、そして「このファイルの実データはどの<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>にあるか」という情報を管理する。』

「<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>…<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>…<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>…<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>…頭がこんがらがってきました」

『順番に説明するから安心しろ。次が<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>、Object Storage Serverだ。<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>は実際のファイルデータを保存するサーバで、それぞれ<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>（Object Storage Target）というストレージデバイスを持つ。ファイルは複数の<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>にストライピングされる。つまり一つの大きなファイルが、複数の<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>に細切れに分散して置かれるんだ。』

「RAIDのストライピングみたいなものですか？」

『似ているが、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のストライピングはネットワーク越しの別サーバに分散する点が違う。例えば100台の<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>に4MBずつストライピングすれば、一つのファイルの読み書きで100台分の帯域を合算できる。これが大帯域を実現する仕組みだ。』

「なるほど！だからファイル一つで数百<ruby>GB<rp>《</rp><rt>ギガバイト</rt><rp>》</rp></ruby>/sも出せるんですね。でも、<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>が一つだと、その<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>がボトルネックにならないんですか？」

『良い指摘だ。初期の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>が単一構成だった。ところがファイル数が10億を超えるような大規模クラスタでは、一つの<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>ではメタデータ性能が足りなくなる。そこで登場したのが<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>、Distributed Namespaceだ。』

「<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>？」

『<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>を使うと、複数の<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>を一つの名前空間に統合できる。つまり<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>と<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>のペアを複数用意して、ディレクトリ単位でどの<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>が管理するかを分散させる。例えば「/project-A」は<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>#1が担当し、「/project-B」は<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>#2が担当する、という具合だ。』

「ディレクトリ単位でメタデータサーバを分担するんですね。それなら<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かにボトルネックは解消できそうです。でも、<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>を使う時に注意することってあるんですか？」

『良い質問だ。<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>には二つのモードがある。一つは「<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby> Static」で、ディレクトリをどの<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>に割り当てるかを管理者が手動で決める。もう一つは「<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby> PFL」、つまりProgressive File Layoutで、ファイルのサイズやアクセスパターンに応じて自動的に最適な<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>を選ぶ。まだ実験的な機能だが、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby> 2.xの後半から徐々に安定化が進んでいる。』

「手動と自動の二種類があるんですね。<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby> Staticだと、後でディレクトリを別の<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>に移動するのは大変そうですが…」

『その通り。一度割り当てたディレクトリを別の<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>に移すのは、基本的にファイルをコピーし直す必要がある。だから導入時によく設計しないといけない。<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby> PFLが安定すればその辺も自動化されるだろう。』

『さらに<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>には<ruby>lnet<rp>《</rp><rt>エルネット</rt><rp>》</rp></ruby>という独自のネットワーク層がある。これは<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>、OmniPath、<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>、TCPなど様々なネットワークを抽象化する仕組みだ。ルーティング機能も持っていて、異なるネットワーク間を中継できる。』

「ネットワークも専用設計なんですか？」

『<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>では<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>が主流だからな。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は最初から<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>を前提に設計されていて、<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>で直接データを転送する。これが低レイテンシの秘密の一つだ。<ruby>lnet<rp>《</rp><rt>エルネット</rt><rp>》</rp></ruby>のルーティング機能を使うと、例えば<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>クラスタとイーサネットクラスタをまたいで<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ファイルシステムを共有できる。』

「異なるネットワークをブリッジできるってことですか？」

『そう。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ルータと呼ばれるノードが<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>とイーサネットの間を取り持つ。これにより、高価な<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>ネットワークを持たない管理用サーバからも、同じ<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ファイルシステムにアクセスできる。』

「<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>のネットワークと言えば<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>が有名ですけど、最近は<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>とかも使われるって聞きました。どう違うんですか？」

『<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>は<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>専用に設計されたネットワークで、スイッチもHCAも<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>向けに最適化されている。<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>は<ruby>RDMA over Converged Ethernet<rp>《</rp><rt>アールディーエムエーオーバーコンバージドイーサネット</rt><rp>》</rp></ruby>の略で、イーサネットの上で<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>を実現する。<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>の利点は既存のイーサネットインフラを流用できることと、コストが比較的安いことだ。ただし、<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>は輻輳管理に注意が必要で、PFC（Priority Flow Control）の設定を誤ると性能が大幅に低下する。』

「じゃあどっちを選べばいいんですか？」

『大規模<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタで最高の性能を求めるなら<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>、汎用的なデータセンタと<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>を統合したいなら<ruby>RoCE<rp>《</rp><rt>ローチェ</rt><rp>》</rp></ruby>が検討される。最近ではNVIDIAのQuantum <ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>とSpectrum Ethernetの両方が使われていて、どちらも<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>との統合実績がある。』

「なるほど…ネットワーク選びもストレージの性能に直結するんですね。ちなみに<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>って、名前の由来は何なんですか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は「Linux」と「クラスター」を組み合わせた造語だ。元々は1999年にCarnegie Mellon大学で始まったプロジェクトで、今はOpenSFSとWhamcloudが中心になって開発を続けている。』

「へえ…20年以上の<ruby>歴史<rp>《</rp><rt>れきし</rt><rp>》</rp></ruby>があるんですね。そういえば<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ってクライアントの接続方法にも特徴があるんですよね？<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>か専用のカーネルモジュールが必要だったような」

『その通り。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>クライアントは専用のカーネルモジュールをロードしたLinuxマシンで動作する。クライアントは<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>にメタデータ操作を要求し、実際のデータ読み書きは<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>と直接やり取りする。この時、クライアントは複数の<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>に同時に接続して、ストライピングされたデータを並列に転送する。』

「ストライピングの設定ってどうやって決めるんですか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ではファイル作成時にstripe_countとstripe_sizeを指定する。stripe_countは何台の<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>に分散するか、stripe_sizeは一つの<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>に書き込むチャンクサイズだ。大規模なシミュレーション出力ならstripe_count=32、stripe_size=4MBといった設定が一般的だ。小ファイルの場合はstripe_count=1にして、逆にオーバーヘッドを減らす。』

「ファイルごとにストライピングの設定を変えられるんですか！」

『そう。ディレクトリ単位でデフォルトのストライピングポリシーを設定できる。/project/Aにはstripe_count=8、/project/Bにはstripe_count=1、といった<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>が可能だ。これが<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の柔軟性の一つだ。加えて<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は拡張属性（xattr）を使って、ファイル個別にストライピング設定を上書きすることもできる。』

「それは便利ですね。そういえば、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>って障害に弱いって聞いたことがあるんですけど。<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>が落ちたらファイルシステム全体が止まるんじゃないですか？」

『良い質問だ。初期の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>が単一障害点だった。しかし今の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>のActive-Standby構成が当たり前だ。二台の<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>サーバを用意して、共有の<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>ストレージを接続する。アクティブ側が死んだらPacemakerが検知して、スタンバイ側が自動的に引き継ぐ。クライアントは数十秒のタイムアウト後に自動再接続するから、アプリケーションからは一時的なハングアップとして見えるだけだ。』

「Pacemaker…LinuxのHAクラスタリングの定番ですね。じゃあ<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>の障害は実質的に問題ないってことですか？」

『完全になくすことはできないが、実用的なレベルでHAは実現できる。ただし<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>自体のデータが壊れた場合は、バックアップからの復元が必要になる。だから<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>は定期的にバックアップを取ることが推奨されている。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>で一番怖いのは<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>障害よりも、メタデータの破損だ。』

「なるほど…<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>にもノウハウが必要なんですね。じゃあ、もう一つの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>も教えてください。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>ってやつです」

『<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>、つまりGeneral Parallel File System。今はIBM <ruby>Spectrum Scale<rp>《</rp><rt>スペクトラムスケール</rt><rp>》</rp></ruby>、さらに最近ではStorage Scaleって呼ばれることも多い。IBMが開発した汎用並列ファイルシステムで、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>とは設計思想が少し違う。』

「どこが違うんですか？」

『まず最大の違いは、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>が完全なPOSIX互換を最重視している点だ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>もPOSIXには準拠しているが、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はより厳密なPOSIXセマンティクスを提供する。特にファイルロックの一貫性が強力で、複数のノードが同じファイルを同時に書き換えても破綻しない。』

「それはすごいですね。でも、その代償みたいなものもあるんですか？」

『ある。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はクローズドソースで、ライセンスコストが高い。また、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>に比べるとコミュニティの情報量が少ない。ただし、その分エンタープライズサポートは手厚い。』

「なるほど…商用とオープンソースの違いって感じですね」

『<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>のアーキテクチャの核になるのがNSD、Network Shared Diskだ。NSDはクラスタ内の全ノードから直接アクセスできる共有ディスクとして機能する。NSDサーバという役割があって、物理ディスクを管理し、他のノードにブロックアクセスを提供する。各ノードはNSDを通じてデータにアクセスするが、メタデータは分散して管理される。』

「<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>みたいに専用のメタデータサーバがいるんですか？」

『<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>は<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>と違って、メタデータサーバという専用の役割がない。全てのノードが対等にメタデータを管理する。この方式を「分散メタデータ管理」と呼ぶ。ファイルの所在情報は全ノードに分散して保持され、障害時にも自動で復旧する。さらに<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はクォーラムという仕組みを持っていて、過半数のノードが生きている限りクラスタ全体が動作し続ける。』

「クォーラム？それってデータベースのクラスタリングで聞いたことがあります」

『そう。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>ではノードにクォーラムノードと非クォーラムノードの二種類の役割がある。クォーラムノードはクラスタの一貫性を保つための投票権を持っていて、過半数のクォーラムノードが稼働していれば、残りのノードがダウンしてもクラスタは動作を継続する。典型的な構成では管理ノード3台をクォーラムノードに指定し、計算ノードは非クォーラムにする。』

「なるほど…じゃあ障害耐性はちゃんと考えられてるんですね。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>にスナップショット機能ってありますか？」

『もちろんある。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はファイルシステム全体のスナップショットを瞬時に取得できる。スナップショットは書き込み時コピー、<ruby>Copy-on-Write<rp>《</rp><rt>コピーオンライト</rt><rp>》</rp></ruby>で実現されていて、作成直後は追加のディスク容量を消費しない。データが更新された時点で差分だけが保存される。典型的には週次でフルスナップショット、日次で差分スナップショットという<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>が推奨されている。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>のスナップショットはディレクトリ単位でも取得できるから、プロジェクトごとにバックアップポリシーを変えることも可能だ。さらに<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>にはファイル暗号化や監査ログといったエンタープライズ機能も充実している。』

「じゃあ<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>より障害に強いんですか？」

『一概には言えない。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の方がPOSIX一貫性は強いが、その分メタデータの更新にオーバーヘッドがかかる。大規模になると<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の方がスケールするという意見もある。そして<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>には<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>という面白い機能がある。』

「<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>？」

『Active File Managementの略だ。<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>は非同期キャッシュ機能で、リモートのファイルシステムをローカルの<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>クラスタにキャッシュできる。例えば東京の<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>クラスタから大阪の<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>クラスタのデータを透過的に読み書きできる。』

「単なるレプリケーションとは違うんですか？」

『違う。<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>はキャッシュなので、実際にデータが必要になった時にだけリモートから取得する。読み取りキャッシュだけでなく、書き込みも非同期で反映できる。つまり「書き込みはローカルに先にして、後でリモートに同期する」という動作が可能だ。』

「いわゆる非同期レプリケーションですね。災害対策にも使えそうです」

『その通り。そして<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>にはCES、Cluster Export Servicesもある。これはNFSやSMB経由で<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>のデータを外部に公開する機能だ。つまり計算ノードはネイティブの<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>クライアントで高速アクセスしつつ、管理用のサーバからはNFSでアクセスする、という使い分けができる。』

「一つのファイルシステムに複数のアクセス手段があるのは便利ですね。でも先輩、最近<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>ってのも注目されてるって聞いたんですけど」

『お、よく知ってるな。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は新しい世代の<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>だ。ソフトウェア定義で、<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>を直結するアプローチが特徴的だ。従来の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>や<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>が<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>やSATA SSDも前提にしていたのに対し、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は最初から<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>専用に設計されている。』

「<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>専用？じゃあ<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>は使えないんですか？」

『アーキテクチャ的に想定していない。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は全てのストレージを<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>で構成し、それをNVoF、つまり<ruby>NVMe over Fabrics<rp>《</rp><rt>エヌブイエムイーオーバーファブリックス</rt><rp>》</rp></ruby>でクラスタ内の全ノードから直接アクセスする。この設計により、エンドツーエンドのレイテンシが100マイクロ秒台を実現している。』

「従来の<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>と比べて桁違いに速いですね」

『そう。さらに<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>の特筆すべき点は、データ削減機能を内蔵していることだ。インラインの重複排除と圧縮をファイルシステムレベルで実装していて、実効容量を2〜5倍に拡大できる。通常、<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>はデータ削減が苦手なんだが、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はそれを克服している。』

「へえ…重複排除と圧縮がファイルシステムネイティブで使えるんですか。それって普通のストレージアレイの機能じゃないですか」

『そう。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は「<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージにエンタープライズストレージの機能を載せる」という発想なんだ。さらにコンテナとの統合も強力で、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>の<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>プラグインが標準提供されている。コンテナが起動するときに瞬時にボリュームをマウントできる。』

「瞬時にってどのくらいの速さなんですか？」

『Podの起動と同時にマウントされるから、実質ゼロ秒だ。従来の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>を<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>で使おうとすると、カーネルモジュールのロードやマウントのタイミング調整が面倒だった。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はユーザ空間のFUSEクライアントも提供していて、コンテナ環境との相性が良い。』

「FUSEクライアント？それって性能的に大丈夫なんですか？」

『良い質問だ。FUSEはユーザ空間でファイルシステムを実装する仕組みで、カーネル空間の実装よりレイテンシが数マイクロ秒増える。ただし<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>の場合、もともと<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>直結でレイテンシが極小なので、FUSEでも実用的な性能が出る。さらにネイティブのカーネルクライアントも用意されていて、最大性能が必要な計算ノードにはそちらを使う。』

「なるほど、用途に応じてクライアントを使い分けるんですね。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>ってデータ保護はどうなってるんですか？」

『<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>を採用している。N+2やN+3の<ruby>パリティ<rp>《</rp><rt>パリティ</rt><rp>》</rp></ruby>構成で、最大3ノード障害まで耐えられる。さらに<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>の面白いところは、データ削減と<ruby>Erasure Coding<rp>《</rp><rt>イレイジャーコーディング</rt><rp>》</rp></ruby>を同時に使っても性能が大きく落ちない設計になっていることだ。これはSIMD命令を活用した高速な圧縮エンジンを実装しているからだ。通常、<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>でデータ削減機能を入れるとレイテンシが悪化するが、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>の性能を活かしたままデータ削減を実現している。』

「それはすごいですね。じゃあ<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>って結構新しい会社ですけど、実績はどうなんですか？」

『<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は2013年設立で、トヨタ自動車やロスアラモス国立研究所などが採用している。特に<ruby>AI/ML<rp>《</rp><rt>エーアイエムエル</rt><rp>》</rp></ruby>トレーニングのデータパイプラインで評価が高い。従来の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ではAI用途にチューニングが難しかった部分を、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は初めからAI向けに設計している。例えばGPUダイレクトストレージに対応していて、GPUがストレージから直接データを読み込める。これにより<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>を経由するオーバーヘッドがなくなり、トレーニングのデータロード時間が大幅に短縮される。』

「なるほど…じゃあ今度は<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>ってのはどうですか？名前だけは聞いたことあります」

『<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はもともとFraunhofer研究所が開発した<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>で、2014年にThinkParQという会社が製品化した。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>に比べて設計がシンプルで、導入が容易なのが特徴だ。』

「どれくらいシンプルなんですか？」

『まず、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のように複雑なモジュール構成ではない。管理コマンドも直感的で、ドキュメントも充実している。そして最大の特徴は、クライアント数に制限がないことだ。さらに<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はサーバコンポーネントが三つのデーモンで構成されている。Management Daemonがクラスタの設定を一元管理し、Metadata Daemonがファイル名やディレクトリ構造を、Storage Daemonが実際のファイルデータを担当する。』

「三つのデーモン…<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>よりずっとシンプルですね」

『そう。設定もbeegfs-ctlという一つのコマンドでほとんど完結する。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のようにlctl、lfs、mkfs.lustreなど複数のツールを覚える必要がない。また、<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>の通信は全部TCPか<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>で行われ、特別なカーネルモジュールが不要なのも利点だ。クライアントもFUSEベースで動作するから、特定のカーネルバージョンに依存しない。』

「へえ…じゃあカーネルアップデートのたびに<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>モジュールをリビルドする必要がないんですね。それは運用楽そうだ」

『まさにそこが<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>の強みだ。ただしFUSEを使う分、カーネルクライアントよりレイテンシは数マイクロ秒増える。計算ノードにとっては気になるレベルだが、管理ノードやファイルサービスには全く問題ない。』

「え？<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>には制限があるんですか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のコミュニティ版にはないが、商用サポート版ではクライアント数に応じたライセンスが必要な場合がある。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>は完全にクライアント数の制限がない。ただし、シンプルさの代償として、初期バージョンではメタデータサーバが単一構成だった。セキュリティの面では、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はKerberosベースの認証とデータ暗号化をサポートしている。一方<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はシンプルさを優先していて、デフォルトでは認証機能が限定的だ。大規模なマルチテナント環境では、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>や<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の方がセキュリティ面で優位と言える。』

「それってボトルネックになりませんか？」

『その通り。一つのメタデータサーバで全てのメタデータ操作を処理するため、クライアント数が増えるとメタデータ性能が頭打ちになる。そこで最近の<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はマルチメタデータに対応した。Buddy Groupという仕組みで、複数のメタデータサーバに負荷を分散できる。』

「じゃあ今は<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>や<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>と同等のスケーラビリティがあるってことですか？」

『規模にもよるが、数千クライアント程度までなら<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>で十分だ。ただし<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>が数万クライアントの実績があるのに対し、<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>の大規模実績はまだ少ない。適材適所で選ぶ必要がある。』

「シンプルで扱いやすいけど、規模が大きくなると<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>や<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の方が安心ってことですね。でも、先輩から見て<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージの<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>で一番大変なのはどんなところですか？」

『一番の難所はバージョンアップだ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のメジャーバージョンアップでは、全ノードのカーネルモジュールを再ビルドして、互換性を確認しながら段階的にアップグレードする必要がある。しかも<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のカーネルモジュールは特定のカーネルバージョンに強く依存するから、OSのアップデートと<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のアップデートを同時に管理しなければならない。これが地味に大変なんだ。』

『そう。設定も「beegfs-ctl」という一つのコマンドでほとんど完結する。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のようにlctl、lfs、mkfs.lustreなど複数のツールを覚える必要がない。このシンプルさが評価されて、中規模の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタや研究機関で導入が進んでいる。』

「ところで先輩、四つも<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>がありますけど、性能的にはどれが一番速いんですか？ベンチマークとか見たことあります？」

『ベンチマークは計測条件によって結果が大きく変わるから注意が必要だ。シーケンシャル読み書きの帯域なら、きちんとチューニングされた<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>が圧倒的だ。特に大規模なストライピングでは、数百台の<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>の帯域を合算できる。しかし、メタデータ操作のレイテンシや小ファイルのランダムアクセスでは、<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>直結の<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>が有利だ。』

「つまり何を計るかで勝者が変わるってことですね」

『そう。だから「どれが速いか」ではなく「どのワークロードで速いか」を考える必要がある。汎用的な<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>シミュレーションには<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>、<ruby>AI/ML<rp>《</rp><rt>エーアイエムエル</rt><rp>》</rp></ruby>には<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>、エンタープライズの高信頼性要件には<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>、手軽さ重視なら<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>というのが大まかな目安だ。ところで、ここまで四つの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を紹介したが、これらのファイルシステムを外部に公開するための技術も重要だ。』

「公開するってどういうことですか？」

『<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタの中には計算ノードだけじゃなくて、管理用のサーバやファイルサーバも存在する。それらはNFSやSMBでファイルシステムにアクセスしたい。そこで登場するのがNFS <ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>だ。』

「<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>？像の神様の名前ですね」

『そう。NFS <ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>はユーザ空間で動作するNFSサーバの実装だ。標準のLinuxカーネルNFSサーバと違い、様々なファイルシステムをバックエンドとしてサポートしている。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>も<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>も<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>も、<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>を通じてNFS公開できる。<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>はFSAL、File System Abstraction Layerというプラグイン機構を持っていて、バックエンドのファイルシステムごとにFSALモジュールをロードする。』

「FSAL…つまりファイルシステムの種類ごとに専用のアダプタがあるってことですね」

『その通り。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>用のFSAL_LUSTRE、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>用のFSAL_<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>、POSIX準拠のファイルシステム用のFSAL_POSIXなどがある。各FSALは、そのファイルシステムの独自機能を最大限活用できるように実装されている。例えばFSAL_LUSTREは<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のストライピング情報をNFSv4の属性マッピングに変換する。』

「なるほど…カーネルのNFSサーバだと<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の拡張属性をNFSにマッピングするのが難しそうですね。でも、カーネル空間じゃなくてユーザ空間で動くって、他に何かメリットがあるんですか？」

『大きなメリットが二つある。一つは、カーネルに依存しないので、異なるファイルシステムのクライアントを簡単に追加できること。二つ目は、NFSv4.1と<ruby>pNFS<rp>《</rp><rt>ピーエヌエフエス</rt><rp>》</rp></ruby>を完全サポートしていることだ。』

「<ruby>pNFS<rp>《</rp><rt>ピーエヌエフエス</rt><rp>》</rp></ruby>って何ですか？」

『Parallel NFSの略だ。通常のNFSでは全てのデータがNFSサーバを経由する。しかし<ruby>pNFS<rp>《</rp><rt>ピーエヌエフエス</rt><rp>》</rp></ruby>では、クライアントが直接ストレージデバイスにアクセスできる。NFSサーバはメタデータの管理だけを行い、実際のデータ転送はクライアントとストレージの間で直接行われる。』

「それってまさに<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>の考え方と同じじゃないですか！」

『その通り。<ruby>pNFS<rp>《</rp><rt>ピーエヌエフエス</rt><rp>》</rp></ruby>はまさに「NFSで<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を実現する」ためのプロトコルだ。<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>を使うと、既存のNFSクライアントから<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>や<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の性能を引き出せる。特にファイルロックの管理が重要で、<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>はNFSv4のファイルロックをしっかり実装している。<ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>はNFSだけでなく、9PプロトコルやSMBもサポートしていて、仮想化環境やWindowsクライアントからのアクセスも可能だ。』

「NFS以外にも対応してるんですか！それは便利ですね。ところで先輩、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージのセキュリティってどうなってるんですか？複数のユーザーが共有するから、権限管理とか暗号化とか気になるんですが」

『良い質問だ。<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージはかつて「閉じたネットワークだから」とセキュリティが軽視される傾向があった。しかし最近はマルチテナント環境やクラウド連携が増えて、セキュリティ要件が厳しくなっている。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はカーネルレベルのクライアントを使うが、接続時にKerberosベースの認証を強制できる。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はロールベースのアクセス制御と監査ログが充実している。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は暗号化とRBACを標準搭載している。』

「ファイルシステムごとに対応が違うんですね。暗号化って、転送中のデータと保存中のデータ、両方あるんですか？」

『そう。転送中の暗号化は<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ではkerberosベースのRPCSEC_GSS、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>ではネイティブの暗号化機能、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は<ruby>TLS<rp>《</rp><rt>ティーエルエス</rt><rp>》</rp></ruby>経由の暗号化をサポートしている。保存中の暗号化は各ストレージノードの<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>ドライブ自体が持っているSED（Self-Encrypting Drive）機能を使うのが一般的だ。ただし、暗号化を有効にすると<ruby>CPU<rp>《</rp><rt>シーピーユー</rt><rp>》</rp></ruby>オーバーヘッドが発生するから、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の性能要件とのバランスが必要だ。』

「やっぱりセキュリティと性能はトレードオフなんですね。では、これらのファイルシステムを監視するツールとかもあるんですか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>にはlctl statsやlfs dfといった基本的なモニタリングコマンドが用意されている。さらにGrafana＋Prometheus＋<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby> Exporterの組み合わせで可視化するのが最近のトレンドだ。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>にはmmmonitorやmmpmonという専用ツールがある。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は専用のWebベース管理コンソールが標準装備で、S3互換APIでの監視も可能だ。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はbeegfs-ctlでほとんどの情報が取得できて、Grafana用のダッシュボードも公開されている。』

「なるほど…運用監視のしやすさも選定基準の一つですね」

『その通り。障害発生時の原因特定のしやすさ、ログの充実度、コミュニティの情報量も重要な要素だ。さて、話が少し脇道に逸れたが、本題に戻すぞ。いくらファイルシステムが速くても、計算ノードからストレージへのネットワークが遅かったら意味ない。その問題を解決するのが<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>だ。』

「<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>？」

『計算ノードのローカル<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>を一時的なキャッシュとして使い、そこから<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>に段階的にデータを書き出す仕組みだ。<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>のアプリケーションは計算結果を定期的にチェックポイントとして保存する。このチェックポイント書き込みが突然大帯域を必要とする「バースト」なんだ。』

「チェックポイントって、アプリケーションの状態を保存することですよね。シミュレーションが何日もかかるから、途中で止まっても再開できるように定期的に保存する」

『その通り。一つのチェックポイントが数<ruby>TB<rp>《</rp><rt>テラバイト</rt><rp>》</rp></ruby>になることも珍しくない。全計算ノードが同時にチェックポイントを書き込もうとすると、ストレージへの負荷が急激に跳ね上がる。<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>はこの書き込みを一度ローカル<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>に受け止めて、その後バックグラウンドで<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>に転送する。』

「つまり、チェックポイントの書き込みをローカルで完結させて、アプリケーションの待ち時間をゼロにするわけですね」

『正解。代表的な実装だと、Cray（現HPE）のDataWarpやDDNのIME、Infinite Memory Engineが有名だ。DataWarpはCrayのスパコンに統合されていて、ジョブスケジューラと連携して<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>領域を動的に割り当てる。ユーザーは特別なAPIを意識せずに、透過的に<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>の恩恵を受けられる。』

「透過的ってどういうことですか？」

『計算ノードから見ると、<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>があたかも通常の<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>の一部のように見える。アプリケーションはいつも通りファイルに書き込むだけで、バックグラウンドで自動的にデータが<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>にフラッシュされる。アプリケーション側でバッファリングを意識する必要がないんだ。』

「DDNのIMEはどう違うんですか？」

『IMEはInfinite Memory Engineの略で、専用の<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>アプライアンスとして提供される。DataWarpがCrayのスパコン専用なのに対し、IMEは汎用的な<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタに導入できる。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>も<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>もバックエンドに使えて、書き込みを一旦IMEに受け止めてから段階的に転送する。最近ではDDNが<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の商用サポートも提供しているから、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby> + IMEの組み合わせが一つの完成されたスタックとして提供されている。』

「<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>とIMEの組み合わせが完成されたスタック…つまり、<ruby>OSS<rp>《</rp><rt>オーエスエス</rt><rp>》</rp></ruby>の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>を自分でチューニングしなくても、商用サポートつきで安定運用できるわけですね」

『そういうことだ。<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>は計算ノードのローカルストレージを使うので、ストレージネットワークの帯域に依存しないという根本的なメリットがある。』

「でも、それって計算ノードに<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>を積むってことですよね？コストがかさむんじゃ…」

『その通り。だから全ての計算ノードに積むのではなく、専用のバーストバッファノードを別に用意する構成もある。例えば「計算ノード256台に対して、バーストバッファノードを16台」という割り当てだ。バーストバッファノードには高速な<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>を大量に搭載し、計算ノードからはネットワーク経由でアクセスする。』

「集中型の<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>ってわけですね。でもそれって、結局ネットワーク帯域がボトルネックにならないんですか？」

『そこが<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>の設計の肝だ。計算ノードからバーストバッファノードへの転送は、<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>やHDRのフル帯域を使う。そしてバーストバッファノードから<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>への転送は、計算の合間などのアイドル時間を利用して行う。つまり「バーストを平滑化」するのが目的だ。』

「なるほど…水の流れを調整するダムみたいなものですね」

『いい例えだ。チェックポイントをダムに一気に流し込んで、その後ゆっくりと下流に流す。これでストレージは常に安定した負荷で<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>できる。最近ではこの<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>の概念が、AI/<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の収束でさらに重要になっている。』

「AIと<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の収束…よく聞く言葉ですが、ストレージ的にはどういうインパクトがあるんですか？」

『従来、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>シミュレーションとAIトレーニングは別々のストレージを使っていた。シミュレーションは大規模な<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>、AIはNASや<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>という具合だ。しかし最近は、シミュレーションの結果をAIで分析したり、AIで生成したモデルをシミュレーションに組み込んだりするワークフローが増えている。』

「データを共有したいってことですね。でもファイルシステムが違うと面倒だ」

『そう。そこで一つの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>でシミュレーションもAIトレーニングも賄いたいというニーズが高まっている。しかし、それぞれのI/Oパターンが全く異なるのが問題だ。』

「どう違うんですか？」

『シミュレーションは大量のデータをシーケンシャルに書き込む。チェックポイントは巨大なファイルで、書き込みパターンは連続的だ。一方、AIトレーニングは大量の小さなファイルをランダムに読み込む。特にデータ拡張やシャッフルのフェーズでは、小さな読み込みが数百万回発生する。』

「一つのファイルシステムで全く異なる二つのパターンを捌くのは難しそうですね」

『その通り。例えば気象シミュレーションを考えてみよう。シミュレーションは3時間おきに50TBのチェックポイントを書き込む。一方で、そのシミュレーションデータをAIで解析して台風の進路予測モデルをトレーニングする場合、数百万枚の2次元スナップショット画像をランダムに読み込む。この全く異なる二つのI/Oパターンを、一つのファイルシステムで同時に処理しなければならない。』

「<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに難しい問題ですね…各ベンダーはどう対応してるんですか？」

『この問題に対して、各ベンダーがそれぞれのアプローチを取っている。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>向けの強みを活かしつつ、小ファイル性能を改善するパッチを投入している。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は初めから両方を想定した設計だ。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>は<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>を使った階層管理で対応する。実際の現場では、シミュレーション用の高速ストレージとAI用の容量向けストレージを論理的に統合する「ユニファイドネームスペース」の需要が高まっている。』

「具体的なユースケースを聞いてもいいですか？」

『例えば創薬の現場を考えてみよう。分子動力学シミュレーションでタンパク質の構造変化を計算し、その結果をAIモデルで解析して新たな薬の候補を絞り込む。このワークフローでは、シミュレーションのチェックポイント（巨大ファイル・シーケンシャル書き込み）と、AIトレーニング用の数百万個の構造スナップショット（小ファイル・ランダム読み込み）が同時に発生する。一つのファイルシステム上で両方を効率よく処理するには、アクセスパターンに応じたデータ配置の最適化が必要になる。』

「なるほど…だからユニファイドネームスペースが重要なんだ」

『もう一つの具体例は自動運転の開発だ。自動運転では実車走行データの収集（大容量シーケンシャル書き込み）と、そのデータを使った深層学習モデルのトレーニング（小ファイルランダム読み込み）を繰り返す。さらにトレーニング済みモデルを使ってシミュレーション上で走行テストを行う。この三つのフェーズが一つのパイプラインとして繋がっている。従来はそれぞれに別々のストレージを用意していたが、AI/<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>収束により一つの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>で統合する動きが加速している。』

「ユニファイドネームスペース？」

『一つのディレクトリツリーとして全てのデータが見えるようにする仕組みだ。例えば/lustre/project/Aの下に、実際には<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>クラスタ上のデータが透過的に見えるようにマウントする。ユーザーからは一つのファイルシステムに見えるが、バックエンドは目的に応じて最適なストレージを使い分ける。』

「それは<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに便利ですね。でも<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>は複雑になりそうです」

『その通り。そこをうまくやるのがストレージ管理者の腕の見せどころだ。AI/<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の収束を実現するには、ストレージだけでなく、ジョブスケジューラやネットワーク構成も含めた全体設計が必要になる。例えばSlurmのジョブスクリプトで「このジョブは<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>の高速パスを使う」といった制御をする。』

「先輩、最近はクラウドでも<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ができるって聞いたんですけど、ストレージはどうなるんですか？」

『良い質問だ。クラウド<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>、いわゆるバースト<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>では、オンプレミスの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>とクラウド上のストレージをどう連携するかが課題になる。一つのアプローチは、クラウド上にも同じファイルシステムを構築して、データを非同期で同期する方法だ。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>はまさにこのユースケースに最適で、オンプレミスの<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>とクラウド上の<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の間で<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>キャッシュを設定できる。』

「なるほど…オンプレとクラウドで同じファイルシステムを使うわけですね」

『もう一つのアプローチは、クラウドネイティブな<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を使う方法だ。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はAWSやAzure上でも動作し、クラウド上のインスタンスだけで完結した<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタを構築できる。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>もAWS上で<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby> as a Serviceとして提供されている。Amazon FSx for <ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>というサービスだ。』

「Amazon FSx for <ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>…聞いたことあります！S3とリンクできるんですよね？」

『その通り。FSx for <ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はS3バケットを<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ファイルシステムとしてマウントできる。S3上のデータを<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のストライピングで高速に読み書きして、計算が終わったら結果をS3に書き戻す。これにより、S3を永続ストレージ、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>を高速キャッシュとして使うハイブリッド構成が実現できる。』

「クラウドとオンプレのハイブリッドを含めると選択肢がさらに広がりますね。そういえば先輩、最近<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>とか新しいファイルシステムも出てきてますよね？」

『良く知ってるな。<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>は<ruby>Intel<rp>《</rp><rt>インテル</rt><rp>》</rp></ruby>が開発した分散<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>で、従来のPOSIX準拠のファイルシステムとは全く異なるアプローチを取っている。POSIXの代わりに独自のNative APIを持っていて、そこから最大の性能を引き出す。特にMPI-IOとの親和性が高く、シミュレーションのチェックポイント性能で従来の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の数倍の性能を出すことがある。』

「POSIXじゃないと互換性が…」

『その通り。<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>は従来のPOSIXアプリケーションとは直接互換性がない。そこで<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>の上にPOSIXエミュレーション層を載せるアプローチが取られている。まだ発展途上だが、次世代の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージとして注目されている。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>も進化を続けていて、2.15以降では性能改善やデータ整合性機能の強化が進んでいる。新しい技術と既存の技術、両方をウォッチし続ける必要がある。』

「<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>って、どこが従来と違うんですか？」

『<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>の最大の違いは「オブジェクトストレージモデル」を採用していることだ。従来のファイルシステムがファイルとディレクトリという階層構造を持つのに対し、<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>はキー・バリューストアに近い。データはコンテナという単位で管理され、各オブジェクトに直接アクセスする。この単純化により、従来のファイルシステムのオーバーヘッドが大幅に削減されている。さらに、<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>はデータの完全性をエンドツーエンドで保証するためのチェックサム機構や、<ruby>RDMA<rp>《</rp><rt>アールディーエムエー</rt><rp>》</rp></ruby>経由のゼロコピーデータ転送を標準搭載している。』

「なるほど…でもPOSIX互換じゃないと従来のアプリケーションが動かないですよね？」

『そのために<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>の上に<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>を載せる「<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby> over <ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>」や、<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>を<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のバックエンドストレージとして使う構成も研究されている。要するに、<ruby>DAOS<rp>《</rp><rt>ダオス</rt><rp>》</rp></ruby>は従来のファイルシステムを置き換えるというより、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージのエコシステムに新しい選択肢を追加するものだと考えていい。』

「要件で選ぶと言われても、ベンチマークとかで性能を比較するにはどうすればいいんですか？」

『<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージのベンチマークには主に二つのツールが使われる。IORはシーケンシャルおよびランダムアクセスの帯域とIOPSを測定する。mdtestはメタデータの性能、つまりファイルの作成・削除・属性変更の速度を測定する。これらのツールはオープンソースで公開されていて、自分でも簡単に試せる。』

「IORとmdtest…名前だけは聞いたことあります。どうやって使うんですか？」

『例えばIORだと「mpirun -np 128 ior -w -r -t 1m -b 16g」のように実行する。これは128プロセスで1MBの転送サイズ、16GBの総データ量で書き込みと読み取りを測定する、という意味だ。mdtestは「mpirun -np 128 mdtest -d /mnt/lustre/test -n 10000」のように使う。128プロセスで各1万ファイルを作成・削除して、そのスループットを計測する。』

「なるほど…実際に計測できるんですね。先輩は普段から使ってるんですか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のチューニングをする時は必ず使う。ストライピングサイズやRPCのサイズを変えながら繰り返し計測して、最適なパラメータを探すんだ。特に<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はmax_mod_rpcs_in_flightやmax_rpcs_in_flightといったパラメータの調整で性能が大きく変わるから、ベンチマークは必須だ。』

「結局、どのファイルシステムを選べばいいんですか？」

『それは要件次第だ。既存の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタが<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>で構築されていて、数万コアのシミュレーションがメインなら<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>が実績十分だ。エンタープライズの<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>でPOSIX一貫性とサポートが重要ななら<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>。AIパイプラインとシミュレーションの両方を低レイテンシで捌きたいなら<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>。手軽に<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を導入したいなら<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>。』

「なるほど…でもそれぞれ一長一短ですね。コストも気になります」

『そうだな。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はソフトウェア自体はオープンソースだが、<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>には高度な知識が必要だ。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はライセンスコストが高いが、サポートが手厚い。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はハードウェアとセットのサブスクリプション型が主流だ。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はオープンソース版と商用サポート版がある。』

「<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>コストも含めてトータルで考える必要があるんですね」

『そう。簡単な選び方の指標を教えてやる。まず、既存の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>クラスタが<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>で組まれていて、大規模シミュレーションが主目的なら<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>一択だ。次に、企業の基幹系<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>で、厳格なPOSIX一貫性とベンダーサポートが必要なら<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>。<ruby>AI/ML<rp>《</rp><rt>エーアイエムエル</rt><rp>》</rp></ruby>パイプラインが主目的で、低レイテンシとデータ削減を両立したいなら<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>。そして、手軽に<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を導入したい中規模の研究機関やスタートアップなら<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>が最適だ。』

「なるほど…四つもあって迷いましたけど、こうやって整理すると選びやすくなりますね」

『もう一つ大事なのは「ロックインされない」という視点だ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はオープンソースだから、ベンダーを変えてもコミュニティ版で<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>を続けられる。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はIBMに完全に依存するが、その分サポート品質は高い。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はプロプライエタリだが、クラウドへのバーストも考慮した設計になっている。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>もデュアルライセンスで、ベンダーロックインは少ない。』

「なるほど…ベンダーロックインのリスクも考慮に入れないといけないんですね。先輩はどのファイルシステムが一番好きなんですか？」

『先輩の好みは聞くな。技術選びは好みじゃなくて要件で決めるもんだ。でもあえて言うなら、俺は<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>だな。20年以上の枯れた技術と、世界中のスパコンでの実績、そしてオープンソースコミュニティの活発さ。何より、トラブルシューティングの情報が豊富なのが運用者にとってはありがたい。』

「<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>推しなんですね。でもそれって先輩がもう使い慣れてるからってのもあるんじゃ…」

『うっ…図星だ。まあそういうこともある。だからこそ、お前は四つ全部をちゃんと触ってみろ。そうすれば自分なりの答えが出るはずだ。』

『ところで、これらのファイルシステムを自分で試したいなら、Dockerや<ruby>Vagrant<rp>《</rp><rt>ベイグラント</rt><rp>》</rp></ruby>で小さなクラスタを組むことができる。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>も<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>対応のDockerイメージが公開されている。』


「マジですか！今週末にでもやってみようかな」

『待て待て。お前、まだ<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のモジュールのビルド方法すら知らないだろ。まずは<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のアーキテクチャをちゃんと理解してからだ。<ruby>DNE<rp>《</rp><rt>ディーエヌイー</rt><rp>》</rp></ruby>を使うなら、少なくとも二つの<ruby>MDT<rp>《</rp><rt>エムディーティー</rt><rp>》</rp></ruby>と四つ以上の<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>を用意する必要がある。』

「それってDockerでできるんですか？」

『できる。ただしカーネルモジュールを使うから、ホストのカーネルバージョンに注意しろ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のバージョンとカーネルの対応表をちゃんと確認しろよ。』

「はい！確認します！…でも、先輩。一つだけ気になることがあるんですけど」

『なんだ？』

「これだけすごい<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>があるのに、何で世の中の普通の会社はみんなNASとかSANを使ってるんですか？」

『いい質問だ。理由は単純で、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージは「専門的すぎる」からだ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>にはLinuxカーネルの深い知識が必要だし、<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>ネットワークの管理も簡単ではない。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>は商用サポートがあるとはいえ、導入コストが桁違いだ。圧倒的な性能は、それに見合う<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>コストと人材を要求する。』

「じゃあ普通の会社にはオーバースペックってことですね」

『そうだ。しかし、データ量がペタバイトを超えたり、GPUクラスタでAIトレーニングをするようになると、NASの限界が見えてくる。その時に「<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>という選択肢がある」と知っているかどうかで、設計の幅が全く変わる。』

「<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに、選択肢を知っておくのは大事ですね。でも、四つもあるとどれを選べばいいか迷っちゃいますよ」

『簡単にまとめてやろう。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>は実績とスケーラビリティが最強で、特に<ruby>InfiniBand<rp>《</rp><rt>インフィニバンド</rt><rp>》</rp></ruby>環境で真価を発揮する。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はPOSIX一貫性とエンタープライズサポートが強みで、大企業の基幹<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>向けだ。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>は<ruby>AI/ML<rp>《</rp><rt>エーアイエムエル</rt><rp>》</rp></ruby>パイプラインと<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>の性能を最大限活かしたい時に最適。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>は手軽に<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>を導入したい中規模クラスタ向けだ。』

「つまり要件によって選ぶってことですね。でも先輩、一つ気になるんですが、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>ってオープンソースなのに商用サポートもあるんですよね？何が違うんですか？」

『コミュニティ版の<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>はOpenSFSが管理していて、誰でも無料で使える。ただしサポートはコミュニティの<ruby>ML<rp>《</rp><rt>エムエル</rt><rp>》</rp></ruby>頼みだ。商用版はWhamcloudやDDN、HPEといったベンダーが提供していて、24時間のサポートとSLA、さらに独自の拡張機能が含まれている。例えばDDNの<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>にはEXAScalerという製品名が付いていて、管理ツールやパフォーマンスモニタリングが追加されている。』

「なるほど…オープンソース版で<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>できるスキルがあればコストを抑えられるけど、足りなければ商用サポートを買う、と」

『正解。逆に<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>はそもそもクローズドソースだから、必ずIBMかパートナー経由でライセンスを購入する必要がある。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>もプロプライエタリで、ハードウェア込みのサブスクリプションが基本だ。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>はコミュニティ版と商用版のデュアルライセンスで、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>に近いモデルだ。』

「<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに…今はまだ必要なくても、選択肢を知っておくのは大事ですね。そういえば先輩、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージって、分野によって使われるファイルシステムに傾向ってあるんですか？」

『ある。アカデミアや研究所では<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>が圧倒的に多い。スパコンセンターはほぼ<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>だ。エンタープライズ、特に金融や製造業の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>では<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の導入実績が多い。官公庁の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ではセキュリティ要件から<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>か<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の商用版が選ばれる。<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>はAIスタートアップやクラウドネイティブな企業で急速にシェアを伸ばしている。<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>は中規模の研究チームや大学の研究室で人気だ。』

「用途によって自然とすみ分けができてるんですね」

『そう。もちろん例外はあるが、これを参考にすれば初めて導入する時にも迷わないだろう。』

「ところで先輩、最近は<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージもオールフラッシュが当たり前って聞いたんですけど、本当ですか？」

『その傾向は強い。従来の<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>ベースの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>だと、一台あたりの<ruby>OST<rp>《</rp><rt>オーエスティー</rt><rp>》</rp></ruby>やNSDの性能が<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>のシーケンシャル性能で制限されていた。しかし<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>が普及してからは、一台のストレージノードで10GB/s以上の帯域を出せるようになった。その結果、必要なノード台数が減り、設置スペースや消費電力も削減できる。』

「<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>の<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>と比べてどうなんですか？」

『例えば<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>ベースで100GB/sを達成しようとすると、一台あたり2GB/sのノードが50台必要だった。しかし<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>ベースなら一台10GB/sのノードが10台で済む。ラック数も消費電力も5分の1になる。ただし、<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>は容量単価が<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>より高いから、大容量ストレージが必要な場合は<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>と<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby>の階層構成を検討することになる。』

「結局、トレードオフなんですね。性能を取るか、容量を取るか」

『そういうことだ。そこを最適化するのがストレージアーキテクトの役目だ。ちなみに<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>ストレージの消費電力は、クラスタ全体の20〜30%を占めることもある。オールフラッシュ化は性能だけでなく、電力効率の面でも大きなメリットがある。』

「えっ…宿題ですか？」

『当然だ。ただし、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のカーネルモジュールのビルドでハマったら、すぐに聞けよ。一人で三日間ハマるより、先輩に五分で聞いた方が生産的だ。』

「はい…わかりました。ところで先輩、一つだけ確認なんですけど」

『なんだ』

「<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>って、要するにSSDキャッシュの<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>版ってことですよね？」

『お、良いところに気づいた。概念的には似ている。ただし、<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>は「計算ジョブの完了を待たせない」という目的に特化している点が違う。通常のSSDキャッシュは「よくアクセスされるデータを高速化する」のが目的だ。<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>は「一気に書き込まれるデータを受け止めて、後でゆっくり処理する」のが目的だ。』

「なるほど…目的が根本的に違うんですね」

『そういうことだ。さて、今日はここまでだ。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のDocker環境ができたら、次は<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>の<ruby>AFM<rp>《</rp><rt>エーエフエム</rt><rp>》</rp></ruby>と<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のHSM機能の違いについて教えてやる。』

「HSM？また新しい単語が…」

『Hierarchical Storage Managementの略だ。要するにホットデータはSSDに、コールドデータは<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>に自動移動する機能だ。これもまた面白いぞ。先週やった<ruby>ストレージ階層化<rp>《</rp><rt>ストレージかいそうか</rt><rp>》</rp></ruby>の<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>版だと思えばいい。』

「あ、先週の階層化の話とつながるんですね！でも<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>の階層化って、もっと大規模なんですよね？」

『そう。通常の階層化が<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>とSSDの間の移動なら、<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>階層化は「<ruby>NVMe<rp>《</rp><rt>エヌブイエムイー</rt><rp>》</rp></ruby><ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby> → <ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby> → テープライブラリ」という三層構成になることもある。データの価値とアクセス頻度に応じて、自動的にデータが移動していく。この制御をポリシーエンジンが担当する。』

「ポリシーエンジン？」

『例えば「30日間アクセスがないファイルはアーカイブ層に移動する」「最終更新から90日経過したプロジェクトディレクトリは読み取り専用にする」といったルールを定義できる。<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>にはHSM（Hierarchical Storage Management）の機能があって、外部のテープライブラリや<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>と連携できる。』

「先輩の話はいつも底がないですね…今日だけで<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>、<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>、NFS <ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>、<ruby>バーストバッファ<rp>《</rp><rt>バーストバッファ</rt><rp>》</rp></ruby>、AI/<ruby>HPC<rp>《</rp><rt>エイチピーシー、High-Performance Computing</rt><rp>》</rp></ruby>収束、クラウド連携…一度に教わりすぎて頭がパンクしそうです」

『一度に全部覚えようとするな。まずは<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のDocker環境を構築して、ファイルのストライピングを実際に体験してみろ。そこから<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>の基本が理解できる。その後、<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>や<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>との違いを調べていけば、自然と知識が整理される。』

「はい！まずは<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のDocker環境から始めます。そういえば、Dockerで<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>を動かすのに、どんなリソースが必要なんですか？」

『最低限、メモリ4GBと空きディスク20GBくらいあれば、MDS1台、OSS2台、クライアント1台の最小構成は動く。カーネルモジュールが必要だから、ホストOSはCentOS 7かRocky Linux 8が無難だ。lctlでモジュールのバージョンを確認して、ホストのカーネルと合ってるかチェックしろ。』

「lctlってコマンド、初めて聞きました。どうやって使うんですか？」

『lctlは<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>の設定やモニタリングを行う万能コマンドだ。例えば「lctl get_param version」で<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のバージョンが確認できる。「lctl list_nids」でネットワークアドレスが分かる。まずは「man lctl」を見て基本的な使い方を覚えろ。Docker環境ができたら、lfsコマンドでストライピングの設定を確認するんだ。』

「了解です！早速今週末に挑戦します！…あ、そういえば先輩、<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のマウントオプションで何か注意することありますか？」

『<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のマウント時はlocalflockとnoflockの使い分けを覚えておけ。アプリケーションがPOSIXファイルロックを使うかどうかで選ぶんだ。とにかくまずは動かしてみろ。理論は後からついてくる。』

「はい！頑張ります！」

『それがストレージの世界だ。一层掘るとまた新しい層が出てくる。永遠に続くぞ。』

新人君は<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>のアーキテクチャ図を眺めながら、先輩の背中を見送った。五種類のファイルシステムの違いを一度に教わったが、まだ頭の中で整理が追いついていない。とりあえず今週末は、Dockerで小さな<ruby>Lustre<rp>《</rp><rt>ラスター</rt><rp>》</rp></ruby>クラスタを組んで、実際にファイルをストライピングしてみることにした。先輩が言っていた<ruby>lnet<rp>《</rp><rt>エルネット</rt><rp>》</rp></ruby>の設定や<ruby><ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby><rp>《</wp><rt>エムディーエス</rt><rp>》</rp></ruby>の冗長化は、実践して初めて理解できるだろう。<ruby>GPFS<rp>《</rp><rt>ジーピーエフエス</rt><rp>》</rp></ruby>のクォーラム、<ruby>WEKA<rp>《</rp><rt>ウィーカ</rt><rp>》</rp></ruby>のNVoF、<ruby>BeeGFS<rp>《</rp><rt>ビージーエフエス</rt><rp>》</rp></ruby>のBuddy Group、NFS <ruby>Ganesha<rp>《</rp><rt>ガネーシャ</rt><rp>》</rp></ruby>のFSAL…今日一日で覚えた単語の多さに、彼は軽い眩暈を覚えながらも、どこかワクワクしていた。三ヶ月後、彼の自宅ラボには四つの<ruby>並列ファイルシステム<rp>《</rp><rt>へいれつファイルシステム</rt><rp>》</rp></ruby>が同時に稼働し、請求書の光熱費が先月比で倍になっていることを、彼はまだ知らない。そしてその翌月、彼の趣味のサーバラックは一枚目のラックを卒業し、二枚目のラックを増設することを検討し始めていた。半年後には、自宅ラボの消費電力が1kWを超え、エアコンを追加で導入する羽目になるのだが、それはまた別の話である。
