import { apiUrl as apiUrl } from "@/constants";
import { ApiError } from "./error";
import { cookies } from "next/headers";

interface RequestOptions {
  method?: string;
  headers?: HeadersInit;
  body?: BodyInit;
  download?: boolean;
  cache?: RequestCache;
  next?: { revalidate: number };
}

const request = async <T>(url: string, options: RequestOptions = {}) => {
  // Auth with Django session
  const cookieStore = cookies();
  const session = cookieStore.get("sessionid")?.value;
  const csrftoken = cookieStore.get("csrftoken")?.value;

  const headers: HeadersInit = {
    Cookie: `sessionid=${session}; csrftoken=${csrftoken}`,
    "X-CSRFToken": csrftoken ?? "",
    Referer: process.env.BACKEND_URL ?? "",
    ...(options.headers || {}),
  };

  const response = await fetch(`${apiUrl}/api/${url}`, {
    method: options.method || "GET",
    headers: headers,
    body: options.body,
    cache: options.cache,
    next: options.next,
  });
  const contentType = response.headers.get("Content-Type");

  if (!response.ok) {
    let errorMessage = "An error occurred";
    if (contentType && contentType.includes("application/json")) {
      try {
        const errorResponse = await response.json();
        errorMessage = errorResponse.detail || errorMessage;
      } catch (error) {
        errorMessage = "Failed to parse error response";
      }
    }
    throw new ApiError(errorMessage, response.status);
  }

  if (options.download) {
    return response.blob() as unknown as T;
  }

  if (response.status === 204) {
    return {} as T;
  }

  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
};

export default request;
