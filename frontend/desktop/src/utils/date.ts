export interface MonthGridDay {
  date: string;
  day: number;
  inMonth: boolean;
}

export function parseLocalDate(value: string): Date {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    throw new Error("日期必须是 YYYY-MM-DD");
  }
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

export function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatMonthKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function getMonthLabel(monthKey: string): string {
  const [year, month] = monthKey.split("-");
  return `${Number(year)}年${Number(month)}月`;
}

export function shiftMonth(monthKey: string, delta: number): string {
  const [year, month] = monthKey.split("-").map(Number);
  return formatMonthKey(new Date(year, month - 1 + delta, 1));
}

export function getMonthGrid(monthKey: string): MonthGridDay[] {
  const [year, month] = monthKey.split("-").map(Number);
  const first = new Date(year, month - 1, 1);
  const start = new Date(year, month - 1, 1 - first.getDay());
  return Array.from({ length: 42 }, (_, index) => {
    const current = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index);
    return {
      date: formatLocalDate(current),
      day: current.getDate(),
      inMonth: current.getMonth() === month - 1,
    };
  });
}

export function isSameLocalDate(left: string, right: string): boolean {
  return left === right;
}

export function isToday(value: string): boolean {
  return value === formatLocalDate(new Date());
}

export function formatReadableDate(value: string): string {
  const date = parseLocalDate(value);
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}
