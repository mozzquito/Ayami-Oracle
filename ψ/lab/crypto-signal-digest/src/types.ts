export interface NewsSource {
  name: string;
  url: string;
}

export interface NewsItem {
  source: string;
  title: string;
  url: string;
}

export type Sentiment = "positive" | "negative" | "neutral";

export interface SentimentResult {
  title: string;
  url: string;
  source: string;
  subject: string; // company/sector/asset mentioned
  sentiment: Sentiment;
  reason: string;
}

export interface IndicatorReading {
  symbol: string;
  rsi: number;
  macdHist: number;
  technicalState: "oversold" | "overbought" | "neutral";
}

export type ConvictionLabel = "HIGH CONVICTION" | "sentiment only";

export interface Signal extends SentimentResult {
  indicator: IndicatorReading | null;
  convictionLabel: ConvictionLabel;
}
