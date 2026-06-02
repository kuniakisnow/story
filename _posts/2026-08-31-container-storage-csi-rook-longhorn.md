---
layout: post
title: "コンテナストレージ ― CSIとRook/Longhorn/Portworxで実現するステートフルコンテナ"
date: 2026-08-31 09:00:00 +0900
tags: [storage, container, kubernetes, csi]
description: "コンテナ環境におけるストレージの課題から、CSI（Container Storage Interface）、Rook/Ceph、Longhorn、Portworx、StatefulSet設計、パフォーマンス考慮点までを解説します。"
---

9月最初の月曜日。新人君が<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>の勉強を始めて1週間が経った。参考書を読みながら、何やら難しい顔をしている。

「先輩、ちょっと質問いいですか？<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>の本を読んでるんですが、『ステートフルなワークロードには<ruby>PersistentVolumeClaim<rp>《</rp><rt>パーシステントボリュームクレーム</rt><rp>》</rp></ruby>を使え』って書いてあるんですけど…そもそもなんでコンテナでストレージがそんなに大変なんですか？」

先輩は手に持っていたキーボードを置いて、ゆっくりと新人君の方に向き直った。

『いい質問だ。まずコンテナの基本をおさらいしよう。コンテナは基本的に**ステートレス**だ。つまり、コンテナを再起動すれば中身は初期状態に戻る。そもそもそういう設計で生まれた技術だ。』

「でもデータベースとか、ちゃんとデータを保存したいPodもありますよね？」

『そう。そこが最初の壁だ。コンテナの中にデータを置くと、Podを再作成した瞬間にデータが消える。だから「コンテナの外」にデータを保存する必要がある。しかもPodが別のノードに移動しても、同じデータにアクセスできなければならない。』

「つまりノード間で共有できるストレージが必要ってことですね」

『その通り。従来は<ruby>iSCSI<rp>《</rp><rt>アイスカジ</rt><rp>》</rp></ruby>やNFSを直接Podにマウントして使ってた。しかしそれではベンダーごとの実装の違いを吸収できず、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のマニフェストがベンダー依存になってしまう。』

「それって移植性が下がりますね。AWSで動かしてたマニフェストがオンプレでそのまま使えない…とか」

『そこで登場したのが**<ruby>Container Storage Interface<rp>《</rp><rt>コンテナストレージインタフェース</rt><rp>》</rp></ruby>**、略して**<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>**だ。<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>はコンテナオーケストレータとストレージシステムの間の標準インタフェースを定義している。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>はv1.13で<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>をGA（一般提供）にした。』

「標準化されたプラグイン機構ってことですね」

『そうだ。<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>以前は、各ストレージベンダーのドライバを<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のコアコードに直接組み込む「in-tree」方式だった。これはメンテナンスが大変で、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のリリースサイクルにベンダーが合わせる必要があった。』

「じゃあ今は？」

『<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>で**out-of-tree**に移行した。ベンダーは自分たちの<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバを独立したコンテナイメージとして配布できる。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のコアコードを変更しなくても、新しいストレージバックエンドを追加できるんだ。』

「それは便利ですね。<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバってどんな種類があるんですか？」

『大きく分けて3種類ある。ブロックストレージ用、ファイルストレージ用、そして<ruby>オブジェクトストレージ<rp>《</rp><rt>オブジェクトストレージ</rt><rp>》</rp></ruby>用だ。AWS EBS、GCE Persistent Disk、Azure Diskは<ruby>ブロック<rp>《</rp><rt>ブロック</rt><rp>》</rp></ruby>用の代表例。NFSやAzure Filesはファイル用。<ruby>MinIO<rp>《</rp><rt>ミニオ</rt><rp>》</rp></ruby>とかはオブジェクト用だ。』

「それぞれのユースケースに合わせて選ぶんですね。でも<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ってどのくらいの規模で動いてるんですか？」

『今や事実上の標準だ。主要なクラウドプロバイダは全部<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバを提供してるし、ストレージベンダーもこぞって<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>対応を打ち出してる。ここからが本題だ。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>ネイティブなストレージソリューションとして、最近注目されてるのが3つある。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>、<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>、そして<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>だ。』

「<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>って初めて聞きました」

『**<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>**は<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>ネイティブな<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>オーケストレーターだ。**<ruby>Operatorパターン<rp>《</rp><rt>オペレーターパターン</rt><rp>》</rp></ruby>**を使って<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>クラスタのデプロイと<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>を自動化する。』

「<ruby>Operatorパターン<rp>《</rp><rt>オペレーターパターン</rt><rp>》</rp></ruby>って、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のカスタムリソース定義を使ってアプリケーションの<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>を自動化する仕組みですよね？前に本で読みました」

『その通り。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>はCephCluster、CephBlockPool、CephFilesystemといったカスタムリソースを定義して、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>のデプロイ、MONの障害復旧、<ruby>PG<rp>《</rp><rt>ピージー</rt><rp>》</rp></ruby>のリバランスを自動でやってくれる。』

「<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>って前回の分散ストレージの話で教わりましたけど、設定がすごく大変って言ってましたよね。それを<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>上でカジュアルに使えるようにする…それが<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>なんですね」

『そう。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>を使うと、<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>のクラスタ構成をYAMLで宣言的に管理できる。<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>を定義すれば、動的プロビジョニングも自動で行われる。PVCを作成すると、<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>のOperatorが自動的に<ruby>RBD<rp>《</rp><rt>アールビーディー</rt><rp>》</rp></ruby>イメージや<ruby>CephFS<rp>《</rp><rt>セフエフエス</rt><rp>》</rp></ruby>ボリュームを作成する。』

「<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>と動的プロビジョニング…それってどういう仕組みですか？」

『<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>は「どのストレージバックエンドを使うか」と「どんなパラメータでプロビジョニングするか」を定義する<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のリソースだ。例えば「SSDなのか<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>なのか」「レプリケーション数はいくつか」「ファイルシステムは何か」といった情報を指定する。』

「じゃあユーザはPVCを作るだけで、<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>の設定に従って自動的にボリュームが作られるんですね」

『そう。<ruby>PersistentVolumeClaim<rp>《</rp><rt>パーシステントボリュームクレーム</rt><rp>》</rp></ruby>にstorageClassNameを指定するだけで、適切なバックエンドからボリュームがプロビジョニングされる。ユーザはストレージの詳細を知らなくていい。』

「それが宣言的な<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>ってやつか…じゃあ次は<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>ですね」

『**<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>**はRancher（現SUSE）が開発した軽量なブロックストレージだ。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>と比べて、ずっとシンプルで<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>に特化してる。』

「軽量ってどのくらい違うんですか？」

『<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>は<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>、MON、MGR、<ruby>MDS<rp>《</rp><rt>エムディーエス</rt><rp>》</rp></ruby>など多数のコンポーネントが必要だ。対して<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>はエンジンとマネージャの2つだけで動く。しかも<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>のエンジンは**マイクロサービス型コントローラ**を採用していて、各ボリュームが独立したコントローラを持つ。』

「ボリュームごとにコントローラがある？それってオーバーヘッドにならないんですか？」

『トレードオフだ。ボリューム単位で独立してるから、あるボリュームの障害が他に影響しない。故障分離が完璧にできる。また<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>は**ビルトインのスナップショットとバックアップ**機能を持ってる。』

「<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>でもスナップショットは取れますよね」

『取れるが、<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>の方が管理が簡単だ。<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby> UIからワンクリックでスナップショットが取れるし、定期的なバックアップスケジュールも設定できる。さらにバックアップ先としてNFSやS3互換ストレージを指定できる。』

「じゃあ小規模な<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>クラスタには<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>で十分ってことですか？」

『そういうことだ。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>はPB級の大規模クラスタに向いてる。対して<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>は数十<ruby>TB<rp>《</rp><rt>テラバイト</rt><rp>》</rp></ruby>〜数PBの規模で、<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>のシンプルさを重視するケースに最適だ。特にエッジコンピューティングや開発環境で人気がある。』

「じゃあエンタープライズの本番環境はどうするんですか？」

『そこで登場するのが**<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>**だ。<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>はエンタープライズ向けのコンテナストレージプラットフォームで、Dell EMCが買収して今はDellの製品ポートフォリオの一部になってる。』

「Dellが…結構大きな会社がやってるんですね」

『<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>の特徴はいくつかある。まず**ストレージプール**の概念だ。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>ノードのローカルSSDや<ruby>HDD<rp>《</rp><rt>エイチディーディー</rt><rp>》</rp></ruby>をプール化して、そこから仮想ボリュームを切り出す。ノードを追加すればプールが自動拡張される。』

「それって<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>と似てませんか？」

『似ているが、<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>はよりエンタープライズ向けの機能が充実してる。例えば**BYOK（Bring Your Own Key）暗号化**だ。KMSと統合して、ボリューム単位で暗号化キーを管理できる。コンプライアンス要件の厳しい金融業界とかで必須の機能だ。』

「セキュリティ面が強化されてるんですね」

『さらに<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>には**STORK**という<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>スケジューラとの連携機能がある。STORKは<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>のデータ配置を考慮してPodのスケジューリングを行う。例えば「このPodはボリュームのあるノードに近い場所にスケジュールしよう」と判断する。』

「データローカリティを考慮したスケジューリングってことですね。それでパフォーマンスが上がる」

『そう。ネットワーク経由のアクセスを減らせるから、レイテンシが改善される。ここで**<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>**の設計についても話しておこう。』

「<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>…本で読んだんですけど、Deploymentと何が違うんですか？」

『<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>はステートフルなアプリケーションのために設計されたワークロードリソースだ。最大の違いは、各Podに**安定したユニークなネットワークID**と**永続的なストレージ**が割り当てられることだ。』

「具体的にはどういうことですか？」

『<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>のマニフェストには**volumeClaimTemplates**というフィールドがある。これを使うと、各Podに対して自動的にPVCが作成される。例えば3つのレプリカを持つ<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>をデプロイすると、web-0、web-1、web-2の3つのPodがそれぞれ自分のPVCを持つ。』

「Podごとに独立したボリュームを持てるんですね」

『そう。DeploymentではすべてのPodが同じPVCを共有する。<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>ではPodごとに異なるPVCを持てる。これがデータベースのクラスタ構成などで重要だ。例えばCassandraやElasticsearchの各ノードは自分専用のデータ領域が必要だからな。』

「なるほど…だからデータベース系は<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>で動かすんですね」

『ただし注意点もある。<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>のPodは**順序立ててデプロイされる**。web-0がReadyになるまでweb-1は起動しない。スケールダウンも逆順だ。この順序制御を理解して設計しないと、アプリケーションの起動に時間がかかる。』

「それは知りませんでした…ところで、コンテナストレージのパフォーマンスってどうなんですか？ローカルに直接SSDを挿すのと比べて？」

『そこが一番重要なポイントだ。コンテナストレージのパフォーマンスは主に2つの要素で決まる。1つは**ローカルSSD vs ネットワークストレージ**の選択、もう1つは**<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>のデータプレーン**の実装方式だ。』

「データプレーンって何ですか？」

『<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>にはコントロールプレーンとデータプレーンがある。コントロールプレーンはボリュームの作成や削除などの管理操作を担当する。データプレーンは実際のI/O処理を担当する。このデータプレーンの実装方式がパフォーマンスに直結する。』

「どんな実装方式があるんですか？」

『大きく2つある。1つは**FUSE（Filesystem in Userspace）ベース**、もう1つは**カーネルモジュールや<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby> Proxyを使う方式**だ。FUSEはユーザ空間でファイルシステムを実装するから開発は簡単だが、カーネル空間とのコンテキストスイッチが発生してパフォーマンスが落ちる。』

「FUSEだとどれくらい遅いんですか？」

『ベンチマークによると、FUSEベースの<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバはネイティブのブロックデバイスと比べてレイテンシが2〜5倍程度悪化することがある。特にランダムI/Oで差が出やすい。』

「じゃあ本番環境はFUSE以外を選ぶべきですね」

『そう。<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>も初期はFUSEベースだったが、今はカーネルモジュール版も提供してる。<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>は独自のカーネルモジュール（px-fuse）を持ってる。<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>はKRBD（カーネル<ruby>RBD<rp>《</rp><rt>アールビーディー</rt><rp>》</rp></ruby>）を使うから、カーネル空間で直接ブロックデバイスを扱える。』

「じゃあ<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>が一番速いんですか？」

『一概には言えない。もう1つの要素として、**ローカルSSD vs ネットワークストレージ**の選択がある。同じノード上のローカルSSDにアクセスするのと、ネットワーク越しに別ノードのストレージにアクセスするのでは、レイテンシに10倍以上の差が出る。』

「じゃあローカルSSDに固定すればいいんじゃないですか？」

『それができれば苦労しない。<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>のPodが別のノードに移動した時、ローカルSSDのデータにはアクセスできない。だから「データの局所性」と「可用性」のバランスを取る必要がある。<ruby>Portworx<rp>《</rp><rt>ポートワークス</rt><rp>》</rp></ruby>のSTORKみたいなスマートスケジューリングが重要になる理由だ。』

「<ruby>確<rp>《</rp><rt>たしか</rt><rp>》</rp></ruby>かに…データをローカルに置きたいけど、ノード障害のことも考えないといけない。トレードオフですね」

『そして最後のピースが**<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>の将来**だ。<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>コミュニティでは、<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバの標準化をさらに進めて、スナップショットやクローン、ボリューム拡張といった機能も<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>の範囲に取り込もうとしている。』

「それってつまり、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>のマニフェストだけでストレージの<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>が完結する未来ってことですか？」

『その通り。<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>と<ruby>PersistentVolumeClaim<rp>《</rp><rt>パーシステントボリュームクレーム</rt><rp>》</rp></ruby>と<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>を適切に組み合わせれば、ストレージ管理者が手動でボリュームを作成する必要がなくなる。アプリケーション開発者がセルフサービスで必要なストレージを要求し、<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>が自動的にプロビジョニングする。』

「それが宣言的な<ruby>運用<rp>《</rp><rt>うんよう</rt><rp>》</rp></ruby>の最終形か…」

先輩は立ち上がって、新人君の肩をポンと叩いた。

『お前、今週でかなり理解が進んだな。来月から本番環境の<ruby>Kubernetes<rp>《</rp><rt>クバネティス</rt><rp>》</rp></ruby>クラスタに<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>/<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>を導入するプロジェクトを任せる。』

「えっ？！私がですか？！」

『ああ。今日学んだことをベースに、<ruby>CSI<rp>《</rp><rt>シーエスアイ</rt><rp>》</rp></ruby>ドライバの選定から<ruby>StorageClass<rp>《</rp><rt>ストレージクラス</rt><rp>》</rp></ruby>の設計、<ruby>StatefulSet<rp>《</rp><rt>ステートフルセット</rt><rp>》</rp></ruby>のマニフェスト作成まで全部自分でやってみろ。もちろんフォローはする。』

「は、はい！頑張ります！」

その夜、新人君は自宅でK3sクラスタを起動し、<ruby>Rook<rp>《</rp><rt>ルーク</rt><rp>》</rp></ruby>をデプロイしようと試みた。しかし<ruby>Ceph<rp>《</rp><rt>セフ</rt><rp>》</rp></ruby>の<ruby>OSD<rp>《</rp><rt>オーエスディー</rt><rp>》</rp></ruby>がCrashLoopBackOffになる問題に深夜まで悩まされ、結局<ruby>Longhorn<rp>《</rp><rt>ロングホーン</rt><rp>》</rp></ruby>でお茶を濁したことは、まだ誰も知らない。
