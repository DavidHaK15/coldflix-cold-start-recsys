// Sinh "poster" cho phim hoàn toàn bằng CSS — màu ổn định theo tên + thể loại.
// Không cần file ảnh hay API ngoài, chạy offline 100%.

const GENRE_HUE: Record<string, number> = {
  Action: 4, Adventure: 28, Animation: 192, Comedy: 45, Crime: 220,
  Documentary: 168, Drama: 280, Fantasy: 265, Horror: 350, Mystery: 235,
  Romance: 330, "Sci-Fi": 200, Thriller: 210, Western: 24, Family: 140, Musical: 312,
};

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export interface PosterStyle {
  background: string;
  accent: string;
  initials: string;
}

export function posterStyle(title: string, genres: string[]): PosterStyle {
  const hash = hashString(title);
  const primaryGenre = genres[0] ?? "Drama";
  const baseHue = GENRE_HUE[primaryGenre] ?? hash % 360;
  const secondHue = (baseHue + 35 + (hash % 40)) % 360;
  const angle = 115 + (hash % 60);

  const c1 = `hsl(${baseHue} 62% 22%)`;
  const c2 = `hsl(${secondHue} 70% 12%)`;
  const accent = `hsl(${baseHue} 85% 64%)`;

  const background = `radial-gradient(120% 120% at 18% 12%, ${accent}22 0%, transparent 42%), linear-gradient(${angle}deg, ${c1} 0%, ${c2} 100%)`;

  const words = title.replace(/\(\d{4}\)/, "").trim().split(/\s+/);
  const initials = words.slice(0, 2).map((w) => w[0]?.toUpperCase() ?? "").join("");

  return { background, accent, initials };
}

// Emoji không được dùng làm icon UI; ở đây chỉ là chữ cái viền mờ trang trí trên poster.
export function matchScore(title: string): number {
  // "% phù hợp" giả lập kiểu Netflix, ổn định theo phim (chỉ để trang trí).
  return 70 + (hashString(title) % 30);
}
