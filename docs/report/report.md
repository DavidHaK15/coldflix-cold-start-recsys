---
title: "Xử lý vấn đề Cold-Start trong Hệ thống Khuyến nghị"
subtitle: "Chủ đề 7 — Môn Xu hướng mới trong ICT (CHKHMT15A1)"
author: "Nhóm thực hiện — Đồ án ColdFlix"
date: "2026"
lang: vi
---

# Tóm tắt

Bài toán *cold-start* (khởi đầu lạnh) là một trong những thách thức cốt lõi của
hệ thống khuyến nghị (Recommender System): khi một người dùng hoặc một sản phẩm
mới xuất hiện mà chưa có đủ dữ liệu tương tác, các mô hình lọc cộng tác
(collaborative filtering) gần như không thể cá nhân hoá. Báo cáo này khảo sát các
hướng giải quyết tiêu biểu trong nghiên cứu và thực tiễn, sau đó hiện thực và
**so sánh trực tiếp năm chiến lược** trên cùng một tập dữ liệu và cùng một thước
đo (Recall@10). Toàn bộ được đóng gói thành một ứng dụng full-stack mô phỏng giao
diện xem phim kiểu Netflix — gọi là **ColdFlix** — nhằm gắn kết nghiên cứu với
trải nghiệm sản phẩm thật. Kết quả thực nghiệm cho thấy không có chiến lược nào
thắng tuyệt đối: chiến lược dựa trên độ phổ biến (popularity) mạnh nhất ở trạng
thái lạnh, trong khi các phương pháp dựa collaborative (Onboarding + Item-CF và
DropoutNet) vượt trội khi người dùng đã có đủ tương tác — củng cố quan điểm rằng
giải pháp hiệu quả là **lai ghép và thích nghi** theo vòng đời dữ liệu.

**Từ khoá:** cold-start, hệ thống khuyến nghị, collaborative filtering,
content-based, onboarding, DropoutNet, learning curve.

# 1. Giới thiệu

Hệ thống khuyến nghị đã trở thành thành phần không thể thiếu của các nền tảng số:
Netflix, YouTube, Amazon, Spotify… Hiệu quả của chúng phần lớn dựa trên việc khai
thác **lịch sử hành vi** của người dùng. Tuy nhiên, mọi hệ thống đều phải đối mặt
với câu hỏi: *làm gì khi chưa có lịch sử?* Đây chính là bài toán cold-start.

Mức độ nghiêm trọng của cold-start không nhỏ. Người dùng mới nếu nhận được gợi ý
kém chất lượng ngay lần đầu sẽ dễ rời bỏ nền tảng; sản phẩm mới nếu không bao giờ
được hiển thị sẽ không thể tích luỹ tương tác, tạo ra vòng lặp bất công
"rich-get-richer". Vì vậy, xử lý cold-start vừa là bài toán kỹ thuật, vừa là bài
toán kinh doanh.

Báo cáo này có ba đóng góp: (1) hệ thống hoá các hướng tiếp cận cold-start và đặt
chúng cạnh nhau để so sánh; (2) hiện thực năm chiến lược cụ thể và đánh giá định
lượng nhất quán trên cùng dữ liệu; (3) tích hợp tất cả vào một ứng dụng demo chạy
được, cho phép quan sát trực quan tác động của từng chiến lược tới trải nghiệm.

# 2. Phát biểu bài toán

Gọi $U$ là tập người dùng, $I$ là tập sản phẩm (ở đây là phim), và $R \in
\mathbb{R}^{|U| \times |I|}$ là ma trận đánh giá, trong đó $r_{u,i}$ là điểm người
dùng $u$ dành cho phim $i$ (đa phần khuyết). Mục tiêu của hệ khuyến nghị là dự
đoán các giá trị khuyết và xếp hạng để chọn ra Top-$N$ phim phù hợp nhất cho mỗi
người dùng.

Ma trận $R$ thường **rất thưa** — trong bộ dữ liệu của chúng tôi độ thưa khoảng
65%. Cold-start là trường hợp đặc biệt nghiêm trọng của tính thưa,
được chia thành ba dạng:

- **New User (người dùng mới):** một dòng của $R$ gần như trống.
- **New Item (sản phẩm mới):** một cột của $R$ gần như trống.
- **New System (hệ thống mới):** toàn bộ $R$ nghèo nàn.

Ứng dụng ColdFlix tập trung vào **New User** (tình huống phổ biến và đo lường
được rõ ràng nhất), đồng thời các chiến lược content-based cũng giải quyết được
**New Item**.

# 3. Tổng quan nghiên cứu liên quan

Cold-start đã được nghiên cứu rộng rãi. Dưới đây là các hướng tiêu biểu cùng đánh
giá ưu/nhược điểm.

| Hướng tiếp cận | Ý tưởng cốt lõi | Ưu điểm | Hạn chế | Tham chiếu |
|---|---|---|---|---|
| Popularity / Non-personalized | Gợi ý sản phẩm phổ biến nhất | Đơn giản, mạnh khi chưa có dữ liệu | Không cá nhân hoá, thiên lệch phổ biến | Baseline kinh điển |
| Content-based | Khớp thuộc tính sản phẩm với hồ sơ sở thích | Xử lý được item mới; không cần dữ liệu cộng đồng | Phụ thuộc chất lượng metadata; thiếu đa dạng (overspecialization) | Schein et al. (2002) |
| Active Learning / Onboarding | Hỏi người dùng vài đánh giá ban đầu, chọn item đa dạng | Thu thập tín hiệu nhanh, làm nền cho CF | Tăng ma sát; bài toán chọn item để hỏi không tầm thường | Rashid et al. (2002) |
| Hybrid nông | Kết hợp tuyến tính content + collaborative | Cân bằng điểm mạnh hai phía | Cần điều chỉnh trọng số thủ công | Burke (2002) |
| Hybrid sâu — DropoutNet | Học biểu diễn lai, dùng dropout để mô phỏng cold-start khi huấn luyện | Chuyển tiếp mượt cold→warm; tốt khi đủ dữ liệu | Phức tạp, cần huấn luyện mạng | Volkovs et al. (2017) |
| Meta-learning — MeLU | Học cách thích nghi nhanh với user mới từ vài mẫu (few-shot) | Thích nghi nhanh, ít dữ liệu | Khó huấn luyện, chi phí tính toán cao | Lee et al. (2019) |
| Wide & Deep / Feature-rich | Kết hợp ghi nhớ (wide) và tổng quát hoá (deep) trên đặc trưng phụ | Tận dụng tốt side-information | Cần hạ tầng đặc trưng phong phú | Cheng et al. (2016) |

**Nhận định.** Các nghiên cứu đồng thuận rằng (i) thông tin phụ (side
information) — nội dung sản phẩm, hồ sơ người dùng — là chìa khoá vượt qua
cold-start; (ii) không tồn tại "viên đạn bạc": mỗi phương pháp mạnh ở một giai
đoạn khác nhau của vòng đời dữ liệu; và (iii) hướng đi bền vững là **lai ghép có
thích nghi** giữa content và collaborative. Tuy nhiên, các công trình thường đánh
giá rời rạc trên những benchmark khác nhau, gây khó khăn khi so sánh trực quan.
Đây chính là khoảng trống mà ColdFlix lấp đầy: so sánh năm chiến lược trên *cùng
một dữ liệu và cùng một thước đo*.

# 4. Phương pháp

## 4.1. Dữ liệu

Chúng tôi sử dụng **76 bộ phim thật nổi tiếng** (The Matrix, Inception, Parasite,
Toy Story…) với **poster, mô tả, năm phát hành lấy thật từ Wikipedia** (qua REST
API, không cần khoá). Phần tương tác (**500 người dùng mô phỏng, ~13.389 lượt đánh
giá**) được *sinh có cấu trúc sở thích* thay vì ngẫu nhiên: ratings sinh từ **sở
thích tiềm ẩn theo thể loại** của từng người dùng cộng với "chất lượng" nội tại
của phim và một lượng nhiễu nhỏ:

$$ r_{u,i} \approx 2.6 + 2.2 \cdot \text{aff}(u,i) + 0.6 \cdot q_i + \epsilon $$

trong đó $\text{aff}(u,i)$ là độ phù hợp giữa sở thích thể loại của $u$ và thể
loại của phim $i$. Nhờ cấu trúc này, cá nhân hoá *thực sự* mang lại lợi ích đo
lường được — điều kiện cần để learning curve có ý nghĩa.

## 4.2. Năm chiến lược

**(1) Popularity-based.** Xếp hạng theo số người dùng từng đánh giá:
$\text{score}(i) = \log(|U_i| + 1)$. Đây là baseline phi cá nhân hoá.

**(2) Content-based Bootstrapping.** Biểu diễn mỗi phim bằng vector TF-IDF trên
thể loại. Hồ sơ người dùng là tổ hợp có trọng số của các phim đã thích (hoặc trực
tiếp từ thể loại yêu thích chọn lúc onboarding). Xếp hạng theo cosine similarity:
$\text{sim}(p, v_i) = \frac{p \cdot v_i}{\lVert p\rVert\,\lVert v_i\rVert}$.

**(3) Onboarding + Item-CF.** Người dùng chấm điểm vài phim đa dạng (active
learning). Sau đó dùng Item-based Collaborative Filtering với độ tương tự cosine
giữa các vector item:
$$ \hat{s}(u,i) = \frac{\sum_{j \in N(i)} \text{sim}(i,j)\, r_{u,j}}{\sum_{j \in N(i)} |\text{sim}(i,j)|} $$

**(4) DropoutNet (đơn giản hoá).** Lấy cảm hứng từ Volkovs et al. (2017): kết hợp
thành phần content và thành phần collaborative (embedding từ TruncatedSVD của ma
trận đánh giá). Trọng số $\alpha$ ưu tiên content khi ít tương tác và giảm dần khi
người dùng "ấm" lên:
$$ \text{score}(i) = \alpha \cdot \text{content}(i) + (1-\alpha)\cdot \text{collab}(i) $$
với $\alpha = 1.0$ khi 0 tương tác, và giảm còn $0.25$ khi $\geq 10$ tương tác.

**(5) Item-CF (Warm).** Dùng toàn bộ lịch sử thật của một người dùng warm làm đối
chứng cho trạng thái đã hết cold-start.

## 4.3. Giao thức đánh giá

Để mô phỏng cold-start một cách công bằng, chúng tôi lấy các người dùng *warm*
(≥25 tương tác), **ẩn ngẫu nhiên một phần lịch sử làm tập holdout**, rồi chỉ "lộ"
$N$ tương tác đầu tiên ($N \in \{0,1,2,5,10,20\}$) cho từng chiến lược như thể đó
là người dùng mới (không dùng `user_id` để tránh rò rỉ holdout). Thước đo là
**Recall@10**:
$$ \text{Recall@10} = \frac{|\text{Top10} \cap \text{Holdout}|}{\min(10, |\text{Holdout}|)} $$
Giá trị được trung bình hoá trên nhiều người dùng để vẽ **learning curve**.

# 5. Hiện thực &amp; Kiến trúc

ColdFlix là ứng dụng full-stack:

- **Frontend** (React 19 + Vite + TypeScript): giao diện xem phim kiểu Netflix —
  hero banner, các hàng carousel poster, hover card, modal chi tiết, luồng
  onboarding, và "Chế độ nghiên cứu" cho phép đổi chiến lược/hồ sơ người dùng và
  thấy gợi ý thay đổi tức thì. Poster là **ảnh phim thật** (lấy từ Wikipedia), có
  **fallback gradient CSS** khi ảnh lỗi/ngoại tuyến.
- **Backend** (FastAPI + scikit-learn): cung cấp REST API
  (`/recommend`, `/catalog`, `/similar`, `/evaluation/learning-curve`…). Lõi
  khuyến nghị dùng `TfidfVectorizer`, cosine similarity và `TruncatedSVD`.
- **Đóng gói**: `docker compose` chạy đồng thời nginx (phục vụ frontend + proxy
  `/api`) và uvicorn (backend) — khởi động cả hệ thống bằng một lệnh.

# 6. Thực nghiệm &amp; Kết quả

Bảng dưới đây là Recall@10 trung bình theo số tương tác ban đầu (60 người dùng
mẫu):

| Chiến lược | 0 | 1 | 2 | 5 | 10 | 20 |
|---|---|---|---|---|---|---|
| Popularity-based | 0.196 | 0.196 | 0.196 | 0.196 | 0.196 | 0.196 |
| Content-based | 0.134 | 0.127 | 0.115 | 0.123 | 0.100 | 0.101 |
| Onboarding + Item-CF | 0.196 | 0.192 | 0.190 | 0.209 | 0.225 | **0.267** |
| DropoutNet | 0.134 | 0.141 | 0.151 | 0.171 | 0.200 | **0.258** |

*(Con số có thể dao động nhẹ giữa các lần chạy do lấy mẫu ngẫu nhiên.)*

**Quan sát chính:**

1. **Tại 0 tương tác (lạnh hoàn toàn):** Popularity đạt 0.196, ngang với Onboarding
   (vốn lùi về popularity khi chưa có tương tác) — gợi ý phổ biến là lựa chọn an
   toàn nhất khi chưa biết gì về người dùng.
2. **Popularity phẳng tuyệt đối:** đường của nó không đổi theo số tương tác — đúng
   bản chất phi cá nhân hoá, không "học" từ hành vi.
3. **Các phương pháp dựa CF vượt lên khi ấm:** Onboarding + Item-CF đạt cao nhất
   (**0.267** tại 20 tương tác), DropoutNet bám sát (**0.258**) — đều vượt
   Popularity ~32–36% nhờ khai thác tín hiệu cộng tác.
4. **Content-based yếu và giảm nhẹ:** chỉ dùng thể loại (đặc trưng thô) nên không
   tận dụng được tương tác tăng thêm.

# 7. Thảo luận

Kết quả của chúng tôi tái hiện đúng các kết luận trong tài liệu:

- Việc **Popularity khó bị đánh bại ở trạng thái lạnh** phù hợp với kinh nghiệm
  thực tiễn và lý do nhiều hệ thống vẫn dùng nó làm fallback mặc định.
- Sự vươn lên của **DropoutNet và Onboarding khi dữ liệu tăng** củng cố luận điểm
  của Volkovs et al. (2017) và Rashid et al. (2002) về hybrid và active learning.
- **Content-based yếu** trong thí nghiệm này vì chỉ dùng thể loại (metadata thô),
  khớp với cảnh báo của Schein et al. (2002) rằng hiệu quả content-based phụ thuộc
  mạnh vào độ giàu của đặc trưng.

Hàm ý thiết kế rõ ràng: một hệ thống thực tế nên **lai ghép có thích nghi** — bắt
đầu bằng popularity/content lúc lạnh, rồi tăng dần trọng số collaborative khi
người dùng tích luỹ tương tác, đúng như cơ chế $\alpha$ trong DropoutNet.

# 8. Hạn chế

- Dữ liệu là synthetic; tuy có cấu trúc sở thích hợp lý nhưng chưa phản ánh đầy đủ
  sự phức tạp của hành vi thật.
- DropoutNet ở đây là bản đơn giản hoá (tổ hợp tuyến tính + SVD), chưa phải mạng
  nơ-ron huấn luyện đầy đủ.
- Content chỉ khai thác thể loại; chưa dùng đạo diễn, diễn viên, mô tả văn bản.
- Chỉ đo Recall@10; chưa đánh giá NDCG, độ đa dạng (diversity) hay độ mới
  (novelty).

# 9. Kết luận &amp; Hướng phát triển

Cold-start là thách thức nền tảng và **không có một chiến lược nào tối ưu cho mọi
giai đoạn**. Thực nghiệm trên ColdFlix cho thấy giải pháp tốt là kết hợp linh hoạt
giữa các họ phương pháp theo lượng dữ liệu sẵn có. Hướng phát triển gồm: dùng
MovieLens thật với đặc trưng phong phú, bổ sung meta-learning (MeLU), mở rộng bộ
thước đo, và tiến tới A/B test trên người dùng thật.

# Tài liệu tham khảo

1. A. I. Schein, A. Popescul, L. H. Ungar, D. M. Pennock. *Methods and Metrics
   for Cold-Start Recommendations.* SIGIR, 2002.
2. A. M. Rashid et al. *Getting to Know You: Learning New User Preferences in
   Recommender Systems.* IUI, 2002.
3. R. Burke. *Hybrid Recommender Systems: Survey and Experiments.* User Modeling
   and User-Adapted Interaction, 2002.
4. M. Volkovs, G. Yu, T. Poutanen. *DropoutNet: Addressing Cold Start in
   Recommender Systems.* NeurIPS, 2017.
5. H. Lee et al. *MeLU: Meta-Learned User Preference Estimator for Cold-Start
   Recommendation.* KDD, 2019.
6. H.-T. Cheng et al. *Wide &amp; Deep Learning for Recommender Systems.* DLRS, 2016.
