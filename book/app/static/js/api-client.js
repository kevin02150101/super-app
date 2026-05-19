// Shared axios client — all async HTTP calls go through here.
(function () {
  if (typeof axios === "undefined") {
    console.error("[apiClient] axios Not loaded yet");
    return;
  }
  const apiClient = axios.create({
    baseURL: "/api/v1",
    timeout: 120000,
    headers: { "Content-Type": "application/json" },
  });

  apiClient.interceptors.response.use(
    (resp) => resp.data,
    (err) => {
      const msg =
        err?.response?.data?.message || err?.message || "Request failed";
      console.error("[API ERROR]", msg, err);
      return Promise.reject(new Error(msg));
    }
  );

  window.apiClient = apiClient;
})();
