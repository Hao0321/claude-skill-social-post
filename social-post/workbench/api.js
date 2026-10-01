const csrf = document.querySelector('meta[name="sp-csrf"]').content;
const messages = {
  invalid_input: "資料格式不正確。請確認必要欄位、JSON schema、時間與識別碼。",
  state_changed: "本機資料已變更或正在使用。請重新驗證，不要沿用舊預覽。",
  local_data_unavailable: "本機資料無法讀取。請檢查資料格式與路徑權限。",
  session_required: "本機連線已過期，請重新整理頁面。",
  request_denied: "請求未通過本機安全檢查，請從工作台首頁重新開啟。",
  body_too_large: "資料超過大小限制。請分成較小的匯入批次。",
  not_found: "找不到這份資料。它可能尚未保存。",
};

export async function api(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      credentials: "same-origin",
      signal: controller.signal,
      headers: body === undefined ? {} : { "Content-Type": "application/json", "X-Social-Post-CSRF": csrf },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(messages[result.error] || "操作未完成，請確認本機服務狀態。");
    return result;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("讀取逾時。草稿與資料不會自動重送，請先確認狀態。");
    if (error instanceof TypeError) throw new Error("本機工作台目前無法連線，請確認啟動程式仍在執行。");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function download(text, name, type = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    throw new Error("剪貼簿無法使用。請選取文字複製，或下載文字檔。");
  }
}
