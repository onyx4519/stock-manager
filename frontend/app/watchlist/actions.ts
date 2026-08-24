"use server";

import { revalidatePath } from "next/cache";
import {
  addWatchlistItem,
  ApiError,
  deleteWatchlistItem,
} from "@/lib/api";


export type WatchlistActionResult = {
  ok: boolean;
  message?: string;
};


function refreshWatchlistViews() {
  revalidatePath("/stocks");
  revalidatePath("/watchlist");
}


export async function addWatchlistAction(
  symbol: string,
): Promise<WatchlistActionResult> {
  try {
    await addWatchlistItem(symbol);
    refreshWatchlistViews();
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof ApiError ? error.message : "관심종목을 추가하지 못했습니다.",
    };
  }
}


export async function deleteWatchlistAction(
  symbol: string,
): Promise<WatchlistActionResult> {
  try {
    await deleteWatchlistItem(symbol);
    refreshWatchlistViews();
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof ApiError ? error.message : "관심종목을 삭제하지 못했습니다.",
    };
  }
}
