"use server";

import { revalidatePath } from "next/cache";
import {
  ApiError,
  createTransaction,
  deleteTransaction,
  updateTransaction,
} from "@/lib/api";
import type { TransactionInput } from "@/types/market";


export type TransactionActionResult = {
  ok: boolean;
  message?: string;
};


function refreshPortfolioViews() {
  revalidatePath("/");
  revalidatePath("/portfolio");
}


export async function saveTransactionAction(
  transactionId: number | null,
  input: TransactionInput,
): Promise<TransactionActionResult> {
  try {
    if (transactionId === null) {
      await createTransaction(input);
    } else {
      await updateTransaction(transactionId, input);
    }
    refreshPortfolioViews();
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof ApiError ? error.message : "거래를 저장하지 못했습니다.",
    };
  }
}


export async function deleteTransactionAction(
  transactionId: number,
): Promise<TransactionActionResult> {
  try {
    await deleteTransaction(transactionId);
    refreshPortfolioViews();
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof ApiError ? error.message : "거래를 삭제하지 못했습니다.",
    };
  }
}
