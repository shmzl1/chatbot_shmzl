import { requestJson } from "./client";
import type { AvatarUploadResponse, HealthResponse, UserPublic } from "../types/user";

export function getMe(): Promise<UserPublic> {
  return requestJson<UserPublic>("/auth/me");
}

export function updateMe(username: string): Promise<UserPublic> {
  return requestJson<UserPublic>("/auth/me", {
    method: "PUT",
    body: JSON.stringify({ username }),
  });
}

export function uploadMyAvatar(file: File): Promise<AvatarUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<AvatarUploadResponse>("/auth/me/avatar", {
    method: "POST",
    body: formData,
  });
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}
