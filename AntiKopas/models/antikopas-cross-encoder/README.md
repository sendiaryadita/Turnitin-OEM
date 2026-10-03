---
tags:
- sentence-transformers
- cross-encoder
- reranker
- generated_from_trainer
- dataset_size:289
- loss:BinaryCrossEntropyLoss
base_model: cross-encoder/ms-marco-MiniLM-L6-v2
pipeline_tag: text-ranking
library_name: sentence-transformers
---

# CrossEncoder based on cross-encoder/ms-marco-MiniLM-L6-v2

This is a [Cross Encoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html) model finetuned from [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) using the [sentence-transformers](https://www.SBERT.net) library. It computes scores for pairs of texts, which can be used for text reranking and semantic search.

## Model Details

### Model Description
- **Model Type:** Cross Encoder
- **Base model:** [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) <!-- at revision 233902d25c440f23af6f7d6e94d2946bac0bee0a -->
- **Maximum Sequence Length:** 512 tokens
- **Number of Output Labels:** 1 label
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Documentation:** [Cross Encoder Documentation](https://www.sbert.net/docs/cross_encoder/usage/usage.html)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Cross Encoders on Hugging Face](https://huggingface.co/models?library=sentence-transformers&other=cross-encoder)

### Full Model Architecture

```
CrossEncoder(
  (0): Transformer({'transformer_task': 'sequence-classification', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'logits'}}, 'module_output_name': 'scores', 'architecture': 'BertForSequenceClassification'})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import CrossEncoder

# Download from the 🤗 Hub
model = CrossEncoder("cross_encoder_model_id")
# Get scores for pairs of inputs
pairs = [
    ['dalam pertempuran Rajasthan. Ekspansi kaum muslim di Eropa Barat ditahan oleh pasukan Kristen dalam pertempuran Tours dan pertempuran sungai Berre. Wilayah tersebut diberi nama Al-Andalus, dan di kemudian hari menjadi Kekhalifan Córdoba. Pada akhir abad ke-15, monarki Kristen di semenanjung Iberia merebut kembali Eropa. Disintegrasi Dinasti Seljuk memicu kebangkitan sejumlah monarki kecil yang bersaing untuk kekuasaan di Anatolia selama periode Perang Salib, hingga masa kebangkitan Kesultanan Utsmaniyah. Kesultanan tersebut berhasil menaklukkan Bizantium pada tahun 1453.Dalam perjalanan sejarahnya, dan setelah berbagai konflik yang dilalui, kekuatan muslim di dunia pada Abad Pertengahan sempat terbagi menjadi sejumlah kekhalifahan dan kesultanan, di antaranya: Seljuk, Ajuuraan, Fatimiyah, Almorawiyah, Adal, Abbasiyah, dan Warsangali di India, Mughal di Somalia, Safawiyah di Persia, dan', 'Pada Senin pagi kami memulai perjalanan ke rumah dengan kereta; namun perjalanan dengan kereta lebih lambat pada hari-hari itu, dan walaupun kami bepergian seharian hingga larut malam, kami belum mencapai rumah di Thelwall hingga hari Selasa, 21 November, pada jam dua pagi, di mana kami membangunkan yang tertidur dengan menyanyikan "Rumahku Istanaku" di bawah jendela kamar tidur di sini timur aula Cuerden, di mana kami tahu ayah dan ibu kami akan menunggu kepulangan kami--seperti yang mereka lakukan sekarang, namun bukan di rumah duniawi. Berita kepulangan kami dengan cepat menyebar di seluruh negeri, di mana kami memang terkenal, dan untuk beberapa waktu kami diperlakukan seperti orang penting dan dikunjungi oleh sejumlah teman- teman, dan tongkat usang kami, yang dulunya ingin kami tinggalkan dalam lautan di Land\'s End, diminta oleh teman dekat dan disimpan dengan baik selama'],
    ['San Juan Bautista yang dinaiki Hasekura dan Luis Sotelo mendarat di Filipina dari Meksiko. Sehabis tiba, San Juan Bautista dibeli penguasa Spanyol. Penguasa setempat tengah menghebatkan kapabilitas proteksi agar melampaui agresi Belanda dan Inggris. Biskop Filipina beserta rakyat domestik Filipina dan pengucap bahasa Tagalog di Manila membeberkan negosiasi Hasekura dengan baginda Spanyol pada sepucuk warkat tertanggal 28 Juli 1619, "Gubernur amat supel terhadap kaum Jepang, dan menanggung suaka terhadap mereka. Sehabis mereka sudah banyak berbelanja benda-benda murah, mereka menetapkan untuk meminjamkan perahu mereka. Kapal itu buru-buru diperbarui demi peperangan. Gubernur belakangan mengambil kapal itu, sebab kelihatan kapal itu indah serta mempunyai kerangka yang teguh, dan kapal-kapal yang ada benar-benar banyak. Nilai untuk kapal itu amat cocok, bagi faedah Yang Mulia."', 'terbentang luas. Tak ada rumah penduduk. Tak ada ladang. Hanya truk-truk besar, mesin backhoe, mesin pengaduk semen, dan para pekerja yang hilir mudik di lahan besar itu. Kugy dan Keenan melongo melihat itu semua. Sakola Alit hilang tanpa bekas. Tanpa buang waktu, mereka mencari penduduk yang masih tersisa, dan bertanya sana-sini. "Bade didamel janten perumahan34, jawab salah satu orang yang berhasil Kugy cegat. Seorang "pengangkut kayu bakar.'],
    ['Kaum Brahmana sepertinya aktif untuk menyebarkan agamanya sebagai upaya untuk menghadapi gempuran aliran agam alain. Di saat yang sama, kesetiaan terhadap kitab Weda telah menjadi tali persatuan yang tipis namun signifikan di antara kalangan agama pribumi. Larson berpendapat bahwa kaum brahmana merespon hal tersebut dengan asimilasi dan konsolidasi. Hal itu tergurat dalam kitab Smerti yang ditulis pada masa itu. Kitab-kitab Smerti mengakui autoritas Weda, menjadikannya kriteria utama untuk membedakan Hindu dan non-Hindu. Gagasan dalam kitab Smerti yang kemudian menjadi insipirasi dasar bagi kebanyakan umat Hindu. Ramayana dan Mahabharata tergolong ke dalam Smerti, yang ditulis pada periode panjang antara zaman Sebelum Masehi dan zaman Masehi. Kitab tersebut berisikan mitologi tentang raja-raja dan pertempuran di masa lampau, dan juga ajaran agama. Sastra Purana yang disusun pada masa', 'Para Brahmanis tampaknya bergiat untuk memperluas perkembangan [agamanya] sebagai maksud untuk menghadapi gempuran aliran-aliran yang lebih heterodoks. Pada saat yang sama, di kalangan agama- agama pribumi yang ada, kesetiaan terhadap kewenangan sastra Weda telah memberikan suatu tali persatuan yang tipis - namun begitu signifikan - di antara kemajemukan dewa-dewi dan praktik keagamaan [yang ada]. Menurut Larson, para brahmana menanggapinya dengan asimilasi dan konsolidasi. Hal tersebut tercerminkan dalam pustaka Smerti yang mulai disusun pada periode itu. Kitab-kitab Smerti dari periode 200 SM-100 M mempermaklumkan kewenangan Weda, sehingga pengakuan terhadap kewenangan Weda menjadi kriteria utama untuk membedakan Hinduisme dengan aliran heterodoks yang menolak Weda. Sebagian besar gagasan dasar dan praktik Hinduisme Klasik berasal dari pustaka Smerti, yang kemudian menjadi inspirasi'],
    ['di antara truk-truk raksasa yang diparkir seenaknya beradu atap. Inilah jejeran toko kelontong dengan konsep menjual di depan warung-warung kopi. Di sana polisi pamong praja, kuli panggul, sopir mobil omprengan, para penjaga malam,', 'berhadapan satu sama lain hampir beradu atap. Inilah jejeran toko kelontong dengan konsep menjual semua jenis barang. Sepeda kami meliuk-liuk di antara truk-truk raksasa yang diparkir seenaknya di depan warung-warung kopi. Di sana hiruk pikuk para karyawan rendahan PN Timah, pengangguran, bromocorah, pensiunan, pemulung besi, polisi pamong praja, kuli panggul, sopir mobil omprengan, para penjaga malam,'],
    ['antara tahun 1200-an hingga 1800-an. Setelah runtuhnya kerajaan Gupta dan Harsha, kekuasaan di India mengalami desentralisasi. Banyak kerajaan kecil berdiri sendiri, dengan wilayah masing-masing yang besar. Kerajaan tersebut dipimpin dengan sistem tuan tanah. Kerajaan yang lebih kecil bergantung pada yang lebih besar. Perpecahan kekuasaan juga berpegaruh pada persaingan agama. Budaya dan bahasa setempat lebih dikedepankan, serta pengaruh Hinduisme-Brahmanis ritualistis memudar. Gerakan rakyat dan kebaktian bermunculan, seiring tumbuhnya aliran Saiwa, Waisnawa, Bhakti, dan Tantra. Agama Buddha mulai redup pada abad ke-9, lalu perhalan menghilang dari India. Seiring dengan dadal yang dialami Dinasti Gupta, tanah-tanah tak bertuan dikumpulkan oleh para Brahmana. Hal ini bukan hanya menjamin keuntungan pertanian dari eksploitasi tanah, namun juga memberikan status baru bagi kelas penguasa.', 'Pada Senin pagi kami memulai perjalanan ke rumah dengan kereta; namun perjalanan dengan kereta lebih lambat pada hari-hari itu, dan walaupun kami bepergian seharian hingga larut malam, kami belum mencapai rumah di Thelwall hingga hari Selasa, 21 November, pada jam dua pagi, di mana kami membangunkan yang tertidur dengan menyanyikan "Rumahku Istanaku" di bawah jendela kamar tidur di sini timur aula Cuerden, di mana kami tahu ayah dan ibu kami akan menunggu kepulangan kami--seperti yang mereka lakukan sekarang, namun bukan di rumah duniawi. Berita kepulangan kami dengan cepat menyebar di seluruh negeri, di mana kami memang terkenal, dan untuk beberapa waktu kami diperlakukan seperti orang penting dan dikunjungi oleh sejumlah teman- teman, dan tongkat usang kami, yang dulunya ingin kami tinggalkan dalam lautan di Land\'s End, diminta oleh teman dekat dan disimpan dengan baik selama'],
]
scores = model.predict(pairs)
print(scores)
# [-2.8892 -4.9106  1.9232  9.1273 -1.9016]

# Or rank different texts based on similarity to a single text
ranks = model.rank(
    'dalam pertempuran Rajasthan. Ekspansi kaum muslim di Eropa Barat ditahan oleh pasukan Kristen dalam pertempuran Tours dan pertempuran sungai Berre. Wilayah tersebut diberi nama Al-Andalus, dan di kemudian hari menjadi Kekhalifan Córdoba. Pada akhir abad ke-15, monarki Kristen di semenanjung Iberia merebut kembali Eropa. Disintegrasi Dinasti Seljuk memicu kebangkitan sejumlah monarki kecil yang bersaing untuk kekuasaan di Anatolia selama periode Perang Salib, hingga masa kebangkitan Kesultanan Utsmaniyah. Kesultanan tersebut berhasil menaklukkan Bizantium pada tahun 1453.Dalam perjalanan sejarahnya, dan setelah berbagai konflik yang dilalui, kekuatan muslim di dunia pada Abad Pertengahan sempat terbagi menjadi sejumlah kekhalifahan dan kesultanan, di antaranya: Seljuk, Ajuuraan, Fatimiyah, Almorawiyah, Adal, Abbasiyah, dan Warsangali di India, Mughal di Somalia, Safawiyah di Persia, dan',
    [
        'Pada Senin pagi kami memulai perjalanan ke rumah dengan kereta; namun perjalanan dengan kereta lebih lambat pada hari-hari itu, dan walaupun kami bepergian seharian hingga larut malam, kami belum mencapai rumah di Thelwall hingga hari Selasa, 21 November, pada jam dua pagi, di mana kami membangunkan yang tertidur dengan menyanyikan "Rumahku Istanaku" di bawah jendela kamar tidur di sini timur aula Cuerden, di mana kami tahu ayah dan ibu kami akan menunggu kepulangan kami--seperti yang mereka lakukan sekarang, namun bukan di rumah duniawi. Berita kepulangan kami dengan cepat menyebar di seluruh negeri, di mana kami memang terkenal, dan untuk beberapa waktu kami diperlakukan seperti orang penting dan dikunjungi oleh sejumlah teman- teman, dan tongkat usang kami, yang dulunya ingin kami tinggalkan dalam lautan di Land\'s End, diminta oleh teman dekat dan disimpan dengan baik selama',
        'terbentang luas. Tak ada rumah penduduk. Tak ada ladang. Hanya truk-truk besar, mesin backhoe, mesin pengaduk semen, dan para pekerja yang hilir mudik di lahan besar itu. Kugy dan Keenan melongo melihat itu semua. Sakola Alit hilang tanpa bekas. Tanpa buang waktu, mereka mencari penduduk yang masih tersisa, dan bertanya sana-sini. "Bade didamel janten perumahan34, jawab salah satu orang yang berhasil Kugy cegat. Seorang "pengangkut kayu bakar.',
        'Para Brahmanis tampaknya bergiat untuk memperluas perkembangan [agamanya] sebagai maksud untuk menghadapi gempuran aliran-aliran yang lebih heterodoks. Pada saat yang sama, di kalangan agama- agama pribumi yang ada, kesetiaan terhadap kewenangan sastra Weda telah memberikan suatu tali persatuan yang tipis - namun begitu signifikan - di antara kemajemukan dewa-dewi dan praktik keagamaan [yang ada]. Menurut Larson, para brahmana menanggapinya dengan asimilasi dan konsolidasi. Hal tersebut tercerminkan dalam pustaka Smerti yang mulai disusun pada periode itu. Kitab-kitab Smerti dari periode 200 SM-100 M mempermaklumkan kewenangan Weda, sehingga pengakuan terhadap kewenangan Weda menjadi kriteria utama untuk membedakan Hinduisme dengan aliran heterodoks yang menolak Weda. Sebagian besar gagasan dasar dan praktik Hinduisme Klasik berasal dari pustaka Smerti, yang kemudian menjadi inspirasi',
        'berhadapan satu sama lain hampir beradu atap. Inilah jejeran toko kelontong dengan konsep menjual semua jenis barang. Sepeda kami meliuk-liuk di antara truk-truk raksasa yang diparkir seenaknya di depan warung-warung kopi. Di sana hiruk pikuk para karyawan rendahan PN Timah, pengangguran, bromocorah, pensiunan, pemulung besi, polisi pamong praja, kuli panggul, sopir mobil omprengan, para penjaga malam,',
        'Pada Senin pagi kami memulai perjalanan ke rumah dengan kereta; namun perjalanan dengan kereta lebih lambat pada hari-hari itu, dan walaupun kami bepergian seharian hingga larut malam, kami belum mencapai rumah di Thelwall hingga hari Selasa, 21 November, pada jam dua pagi, di mana kami membangunkan yang tertidur dengan menyanyikan "Rumahku Istanaku" di bawah jendela kamar tidur di sini timur aula Cuerden, di mana kami tahu ayah dan ibu kami akan menunggu kepulangan kami--seperti yang mereka lakukan sekarang, namun bukan di rumah duniawi. Berita kepulangan kami dengan cepat menyebar di seluruh negeri, di mana kami memang terkenal, dan untuk beberapa waktu kami diperlakukan seperti orang penting dan dikunjungi oleh sejumlah teman- teman, dan tongkat usang kami, yang dulunya ingin kami tinggalkan dalam lautan di Land\'s End, diminta oleh teman dekat dan disimpan dengan baik selama',
    ]
)
# [{'corpus_id': ..., 'score': ...}, {'corpus_id': ..., 'score': ...}, ...]
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 289 training samples
* Columns: <code>text_a</code>, <code>text_b</code>, and <code>label</code>
* Approximate statistics based on the first 100 samples:
  |          | text_a                                                                               | text_b                                                                               | label                                           |
  |:---------|:-------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------|:------------------------------------------------|
  | type     | string                                                                               | string                                                                               | int                                             |
  | modality | text                                                                                 | text                                                                                 |                                                 |
  | details  | <ul><li>min: 18 tokens</li><li>mean: 245.33 tokens</li><li>max: 376 tokens</li></ul> | <ul><li>min: 20 tokens</li><li>mean: 292.58 tokens</li><li>max: 377 tokens</li></ul> | <ul><li>0: ~50.96%</li><li>1: ~49.04%</li></ul> |
* Samples:
  | text_a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | text_b                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | label          |
  |:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------|
  | <code>menimbulkan penafsiran ganda. Penulis dan pembaca bisa mempunyai pemahaman yang berbeda. Apa yang dituliskan oleh penulis terkadang diartikan berbeda oleh pembaca. Pemahaman pembaca mengenai konteks penulisan sebuah teks merupakan sebuah faktor yang mendukung untuk memahami sebuah teks.</code>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | <code>Benda-benda di sekelilingku-pohon-pohon, semak-semak... rumah-semua mulai terlihat sangat rapuh. Berharap semoga tak ada pohon di seberang sungai yang menjadi kesayangan Esme, aku mulai berlari. Kemudian berhenti waktu gaun satin ketatku robek sepanjang lima belas sentimeter di bagian paha. Alice! Well, karena Alice selama ini memang selalu menganggap pakaian sebagai benda sekali pakai dan mudah digantikan, ia pasti takkan mempermasalahkan hal ini. Hati-hati aku membungkuk dan mencengkeram ujung gaun sebelah kanan yang belum robek, lalu, dengan mengerahkan sedikit tenaga saja, merobek gaun itu hingga pangkal paha. Berikutnya, aku menyesuaikan robekan di sebelah kiri. Begini lebih nyaman. Aku bisa mendengar suara tawa teredam di rumah, bahkan suara seseorang mengertakkan gigi. Suara tawa itu berasal dari lantai atas dan bawah, dan dengan mudah aku bisa mengenali suara tawa kasar dan</code>    | <code>0</code> |
  | <code>untuk bertempur. Pasukan pemberontak menyerang di Labraunda. Mereka kalah lagi dan bahkan lebih parah. Kekalahan ini juga sangat dirasakan oleh pasukan Miletos. Karia kembali diserbu setelah pemberontak menang berkali-kali. Perlawanan kecil masih terus diusahakan selagi pemberontak menuju Karia. Terjadinya pertempuran Pedasos adalah dengan tujuan ini. Pasukan Karia menunggu untuk menyergap di Pedasos hingga malam hari dan mereka ternyata menang. Pasukan pemberontak dari Persia itu rugi besar. Pemimpin pasukan pemberontak ini pun dibunuh. Ini memiliki dampak lain dalam aspek-aspek pemerintahan di Karia sekitar tahun 495 SM. Pasukan Persia tidak menyerah setelah kekalahan tadi dan menyerang Ionia dan Aiolia. Mereka merebut kembali Klazomenai dan Kyme. Mereka tidak terlalu aktif selama beberapa waktu karena bencana di Karia. Karena perasaannya tak enak, pemimpin pasukan Miletos</code> | <code>Mereka berpikir apakah harus menyerah kepada Persia atau bersama-sama pergi dari Asia Kecil. Kerika sedang membicarakan pilihan-pilihan itu, mereka didatangi oleh pasukan Miletos, dan dengan tambahan tentara ini mereka memutuskan untuk terus bertempur. Pasukan Persia menyerang mereka di Labraunda, dan mengalahkan mereka dengan memberikan kerugian yang bahkan lebih besar, dengan pasukan Miletos khususnya menderita kerugian yang buruk. Pertempuran Pedasos Setelah kemenangan ganda atas orang Karia, Daurises mulai menyerbu benteng-benteng Karia. Orang Karia masih terus melakukan perlawanan, dan memutuskan untuk menyergap Dariuses di jalan menuju Pedasos. Herodotos menyiratkan bahwa ini kurang lebih terjadi tidak lama setelah Pertempuran Labraunda, namun diduga pula bahwa peristiwa di Pedasos terjadi setahun setelahnya, yaitu pada tahun 496 SM, sehingga memberi cukup waktu bagi orang Karia</code> | <code>1</code> |
  | <code>pangeran memberi hormat kepada Garrofat dan menerima tugas tersebut beserta semua lubang rahasia. Karena banyak yang kau pertaruhkan, kau diperkenankan untuk memberikan kata-kata tidak bisa mengenali orang asing tinggi yang berdiri di samping Azalia; mukanya tersamarkan lipatan terakhir. Kemudian, dia pun sedikit bertanya-tanya kemanakah para petugas dan pejabat kerajaan, dan Saat itulah untuk pertama kalinya Bright-Wits menyadari ketidakhadiran Ablano, sang Brahma. Dia pun Setelah Garrofat selesai berbicara, dia bertanya, "Apakah aku harus</code>                                                                                                                                                                                                                                                                                                                                                      | <code>Kemudian, dengan suara yang tenang dan jelas dia bertanya, "Apakah aku harus mengerjakannya sekarang?" "Sekarang juga, seru Garrofat. Sekarang, selagi penjagamu sedang tidak ada. Saat itulah untuk pertama kalinya Bright-Wits menyadari ketidakhadiran Ablano, sang Brahma. Dia pun tidak bisa mengenali orang asing tinggi yang berdiri di samping Azalia; mukanya tersamarkan lipatan jubahnya. Kemudian, dia pun sedikit bertanya-tanya kemanakah para petugas dan pejabat kerajaan, dan apa aura misterius yang sepertinya meliputi seluruh ruangan ini.</code>                                                                                                                                                                                                                                                                                                                                                                   | <code>1</code> |
* Loss: [<code>BinaryCrossEntropyLoss</code>](https://sbert.net/docs/package_reference/cross_encoder/losses.html#binarycrossentropyloss) with these parameters:
  ```json
  {
      "activation_fn": "torch.nn.modules.linear.Identity",
      "pos_weight": null
  }
  ```

### Evaluation Dataset

#### Unnamed Dataset

* Size: 36 evaluation samples
* Columns: <code>text_a</code>, <code>text_b</code>, and <code>label</code>
* Approximate statistics based on the first 36 samples:
  |          | text_a                                                                               | text_b                                                                               | label                                           |
  |:---------|:-------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------|:------------------------------------------------|
  | type     | string                                                                               | string                                                                               | int                                             |
  | modality | text                                                                                 | text                                                                                 |                                                 |
  | details  | <ul><li>min: 10 tokens</li><li>mean: 256.19 tokens</li><li>max: 339 tokens</li></ul> | <ul><li>min: 74 tokens</li><li>mean: 298.78 tokens</li><li>max: 372 tokens</li></ul> | <ul><li>0: ~52.78%</li><li>1: ~47.22%</li></ul> |
* Samples:
  | text_a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | text_b                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | label          |
  |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------|
  | <code>dalam pertempuran Rajasthan. Ekspansi kaum muslim di Eropa Barat ditahan oleh pasukan Kristen dalam pertempuran Tours dan pertempuran sungai Berre. Wilayah tersebut diberi nama Al-Andalus, dan di kemudian hari menjadi Kekhalifan Córdoba. Pada akhir abad ke-15, monarki Kristen di semenanjung Iberia merebut kembali Eropa. Disintegrasi Dinasti Seljuk memicu kebangkitan sejumlah monarki kecil yang bersaing untuk kekuasaan di Anatolia selama periode Perang Salib, hingga masa kebangkitan Kesultanan Utsmaniyah. Kesultanan tersebut berhasil menaklukkan Bizantium pada tahun 1453.Dalam perjalanan sejarahnya, dan setelah berbagai konflik yang dilalui, kekuatan muslim di dunia pada Abad Pertengahan sempat terbagi menjadi sejumlah kekhalifahan dan kesultanan, di antaranya: Seljuk, Ajuuraan, Fatimiyah, Almorawiyah, Adal, Abbasiyah, dan Warsangali di India, Mughal di Somalia, Safawiyah di Persia, dan</code> | <code>Pada Senin pagi kami memulai perjalanan ke rumah dengan kereta; namun perjalanan dengan kereta lebih lambat pada hari-hari itu, dan walaupun kami bepergian seharian hingga larut malam, kami belum mencapai rumah di Thelwall hingga hari Selasa, 21 November, pada jam dua pagi, di mana kami membangunkan yang tertidur dengan menyanyikan "Rumahku Istanaku" di bawah jendela kamar tidur di sini timur aula Cuerden, di mana kami tahu ayah dan ibu kami akan menunggu kepulangan kami--seperti yang mereka lakukan sekarang, namun bukan di rumah duniawi. Berita kepulangan kami dengan cepat menyebar di seluruh negeri, di mana kami memang terkenal, dan untuk beberapa waktu kami diperlakukan seperti orang penting dan dikunjungi oleh sejumlah teman- teman, dan tongkat usang kami, yang dulunya ingin kami tinggalkan dalam lautan di Land's End, diminta oleh teman dekat dan disimpan dengan baik selama</code>        | <code>0</code> |
  | <code>San Juan Bautista yang dinaiki Hasekura dan Luis Sotelo mendarat di Filipina dari Meksiko. Sehabis tiba, San Juan Bautista dibeli penguasa Spanyol. Penguasa setempat tengah menghebatkan kapabilitas proteksi agar melampaui agresi Belanda dan Inggris. Biskop Filipina beserta rakyat domestik Filipina dan pengucap bahasa Tagalog di Manila membeberkan negosiasi Hasekura dengan baginda Spanyol pada sepucuk warkat tertanggal 28 Juli 1619, "Gubernur amat supel terhadap kaum Jepang, dan menanggung suaka terhadap mereka. Sehabis mereka sudah banyak berbelanja benda-benda murah, mereka menetapkan untuk meminjamkan perahu mereka. Kapal itu buru-buru diperbarui demi peperangan. Gubernur belakangan mengambil kapal itu, sebab kelihatan kapal itu indah serta mempunyai kerangka yang teguh, dan kapal-kapal yang ada benar-benar banyak. Nilai untuk kapal itu amat cocok, bagi faedah Yang Mulia."</code>            | <code>terbentang luas. Tak ada rumah penduduk. Tak ada ladang. Hanya truk-truk besar, mesin backhoe, mesin pengaduk semen, dan para pekerja yang hilir mudik di lahan besar itu. Kugy dan Keenan melongo melihat itu semua. Sakola Alit hilang tanpa bekas. Tanpa buang waktu, mereka mencari penduduk yang masih tersisa, dan bertanya sana-sini. "Bade didamel janten perumahan34, jawab salah satu orang yang berhasil Kugy cegat. Seorang "pengangkut kayu bakar.</code>                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | <code>0</code> |
  | <code>Kaum Brahmana sepertinya aktif untuk menyebarkan agamanya sebagai upaya untuk menghadapi gempuran aliran agam alain. Di saat yang sama, kesetiaan terhadap kitab Weda telah menjadi tali persatuan yang tipis namun signifikan di antara kalangan agama pribumi. Larson berpendapat bahwa kaum brahmana merespon hal tersebut dengan asimilasi dan konsolidasi. Hal itu tergurat dalam kitab Smerti yang ditulis pada masa itu. Kitab-kitab Smerti mengakui autoritas Weda, menjadikannya kriteria utama untuk membedakan Hindu dan non-Hindu. Gagasan dalam kitab Smerti yang kemudian menjadi insipirasi dasar bagi kebanyakan umat Hindu. Ramayana dan Mahabharata tergolong ke dalam Smerti, yang ditulis pada periode panjang antara zaman Sebelum Masehi dan zaman Masehi. Kitab tersebut berisikan mitologi tentang raja-raja dan pertempuran di masa lampau, dan juga ajaran agama. Sastra Purana yang disusun pada masa</code>   | <code>Para Brahmanis tampaknya bergiat untuk memperluas perkembangan [agamanya] sebagai maksud untuk menghadapi gempuran aliran-aliran yang lebih heterodoks. Pada saat yang sama, di kalangan agama- agama pribumi yang ada, kesetiaan terhadap kewenangan sastra Weda telah memberikan suatu tali persatuan yang tipis - namun begitu signifikan - di antara kemajemukan dewa-dewi dan praktik keagamaan [yang ada]. Menurut Larson, para brahmana menanggapinya dengan asimilasi dan konsolidasi. Hal tersebut tercerminkan dalam pustaka Smerti yang mulai disusun pada periode itu. Kitab-kitab Smerti dari periode 200 SM-100 M mempermaklumkan kewenangan Weda, sehingga pengakuan terhadap kewenangan Weda menjadi kriteria utama untuk membedakan Hinduisme dengan aliran heterodoks yang menolak Weda. Sebagian besar gagasan dasar dan praktik Hinduisme Klasik berasal dari pustaka Smerti, yang kemudian menjadi inspirasi</code> | <code>1</code> |
* Loss: [<code>BinaryCrossEntropyLoss</code>](https://sbert.net/docs/package_reference/cross_encoder/losses.html#binarycrossentropyloss) with these parameters:
  ```json
  {
      "activation_fn": "torch.nn.modules.linear.Identity",
      "pos_weight": null
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `learning_rate`: 2e-05
- `warmup_steps`: 0.1
- `load_best_model_at_end`: True

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 8
- `num_train_epochs`: 3
- `max_steps`: -1
- `learning_rate`: 2e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0.1
- `optim`: adamw_torch_fused
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1.0
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: False
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: None
- `trackio_bucket_id`: None
- `trackio_static_space_id`: None
- `per_device_eval_batch_size`: 8
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: True
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `dataloader_multiprocessing_context`: None
- `dataloader_in_order`: True
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_static_graph`: None
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: None
- `fsdp_config`: None
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: proportional
- `router_mapping`: {}
- `learning_rate_mapping`: {}
- `warmup_ratio`: None

</details>

### Training Logs
| Epoch   | Step    | Training Loss | Validation Loss |
|:-------:|:-------:|:-------------:|:---------------:|
| 0.2703  | 10      | 0.7013        | -               |
| 0.5405  | 20      | 0.5434        | -               |
| 0.8108  | 30      | 0.7016        | -               |
| 1.0     | 37      | -             | 0.5396          |
| 1.0811  | 40      | 0.5086        | -               |
| 1.3514  | 50      | 0.6007        | -               |
| 1.6216  | 60      | 0.3029        | -               |
| 1.8919  | 70      | 0.2025        | -               |
| 2.0     | 74      | -             | 0.3074          |
| 2.1622  | 80      | 0.3267        | -               |
| 2.4324  | 90      | 0.5156        | -               |
| 2.7027  | 100     | 0.2110        | -               |
| 2.9730  | 110     | 0.2083        | -               |
| **3.0** | **111** | **-**         | **0.1866**      |

* The bold row denotes the saved checkpoint.

### Training Time
- **Training**: 10.9 minutes
- **Evaluation**: 8.7 seconds
- **Total**: 11.1 minutes

### Framework Versions
- Python: 3.13.0
- Sentence Transformers: 6.1.0
- Transformers: 5.17.0
- PyTorch: 2.14.0+cpu
- Accelerate: 1.15.0
- Datasets: 5.0.1
- Tokenizers: 0.23.2

## Additional Resources

- [Training and Finetuning Reranker Models with Sentence Transformers](https://huggingface.co/blog/train-reranker): the end-to-end guide for training or finetuning Cross Encoder (reranker) models.
- [Multimodal Embedding & Reranker Models with Sentence Transformers](https://huggingface.co/blog/multimodal-sentence-transformers): use text, image, audio, and video reranker models through the same API.
- [Training and Finetuning Multimodal Embedding & Reranker Models with Sentence Transformers](https://huggingface.co/blog/train-multimodal-sentence-transformers): training multimodal Cross Encoders.

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->