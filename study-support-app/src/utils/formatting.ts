/**
 * 金額を通貨フォーマットで表示する
 * @param amount 金額
 * @param currency 通貨コード（デフォルト: 'jpy'）
 * @returns フォーマットされた金額文字列
 */
export const formatAmount = (amount: number, currency: string = 'jpy'): string => {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 0
  }).format(amount);
}; 