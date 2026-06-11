import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, ImagePlus, Save } from "lucide-react";
import { useState } from "react";
import { getHealth, getMe, updateMe, uploadMyAvatar } from "../api/userApi";
import { resolveAssetUrl } from "../api/client";
import { Button } from "../components/ui/Button";
import { TextField } from "../components/ui/TextField";
import { StickyCard } from "../components/paper/StickyCard";
import { useAppStore } from "../stores/appStore";

export function SettingsPage() {
  const queryClient = useQueryClient();
  const backendUrl = useAppStore((state) => state.backendUrl);
  const updateBackendUrl = useAppStore((state) => state.updateBackendUrl);
  const [backendDraft, setBackendDraft] = useState(backendUrl);
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const healthQuery = useQuery({ queryKey: ["health", backendUrl], queryFn: getHealth, retry: 0 });
  const [username, setUsername] = useState("");

  const profileMutation = useMutation({
    mutationFn: () => updateMe(username || meQuery.data?.username || "我"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const avatarMutation = useMutation({
    mutationFn: uploadMyAvatar,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const user = meQuery.data;

  return (
    <div className="grid h-full grid-cols-[minmax(520px,1fr)_360px] gap-5 overflow-hidden">
      <section className="soft-panel overflow-auto rounded-[28px] p-6">
        <h2 className="text-2xl font-black">设置</h2>
        <div className="mt-6 grid gap-5">
          <StickyCard>
            <h3 className="mb-4 text-lg font-black">本地用户</h3>
            <div className="flex items-center gap-4">
              {user?.avatar_url ? (
                <img className="size-20 rounded-[24px] object-cover" src={resolveAssetUrl(user.avatar_url)} alt={user.username} />
              ) : (
                <div className="grid size-20 place-items-center rounded-[24px] bg-[rgba(98,119,90,0.15)] text-2xl font-black text-[var(--green)]">
                  我
                </div>
              )}
              <div className="grid flex-1 gap-3">
                <TextField
                  label="显示 ID / 用户名"
                  placeholder={user?.username || "我"}
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />
                <div className="flex gap-2">
                  <Button variant="primary" onClick={() => profileMutation.mutate()}>
                    <Save size={16} />
                    保存用户名
                  </Button>
                  <label className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--line)] bg-[var(--surface)] px-4 text-sm font-bold text-[var(--green)]">
                    <ImagePlus size={16} />
                    上传头像
                    <input
                      className="hidden"
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (file) {
                          avatarMutation.mutate(file);
                        }
                        event.target.value = "";
                      }}
                    />
                  </label>
                </div>
              </div>
            </div>
          </StickyCard>

          <StickyCard>
            <h3 className="mb-4 text-lg font-black">后端地址</h3>
            <div className="grid gap-3">
              <TextField value={backendDraft} onChange={(event) => setBackendDraft(event.target.value)} />
              <div className="flex flex-wrap gap-2">
                {["http://127.0.0.1:8000", "http://127.0.0.1:8010", "http://127.0.0.1:18000"].map((url) => (
                  <Button key={url} variant="ghost" onClick={() => setBackendDraft(url)}>
                    {url.replace("http://", "")}
                  </Button>
                ))}
              </div>
              <Button
                variant="primary"
                onClick={() => {
                  updateBackendUrl(backendDraft);
                  void queryClient.invalidateQueries();
                }}
              >
                保存后端地址
              </Button>
            </div>
          </StickyCard>
        </div>
      </section>

      <aside className="grid min-h-0 gap-5 overflow-auto">
        <StickyCard>
          <h3 className="mb-2 text-lg font-black">连接状态</h3>
          <p className="text-sm leading-6 text-[var(--muted)]">
            {healthQuery.data?.status === "ok" ? "后端连接正常。" : healthQuery.error instanceof Error ? healthQuery.error.message : "正在检查后端。"}
          </p>
        </StickyCard>
        <StickyCard>
          <h3 className="mb-2 text-lg font-black">角色与记忆</h3>
          <p className="text-sm leading-6 text-[var(--muted)]">
            角色管理、记忆管理和人设编辑属于嵌入能力，后续放入设置的高级区域，不作为一级主功能。
          </p>
        </StickyCard>
        <Dialog.Root>
          <Dialog.Trigger asChild>
            <Button variant="secondary">
              <ExternalLink size={16} />
              第三方开源声明
            </Button>
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm" />
            <Dialog.Content className="fixed left-1/2 top-1/2 z-40 w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-[28px] bg-[var(--surface)] p-6 shadow-paper">
              <Dialog.Title className="text-xl font-black">第三方开源声明</Dialog.Title>
              <Dialog.Description className="mt-3 text-sm leading-7 text-[var(--muted)]">
                桌面端 UI、样式和布局方向参考 floral-notepaper 与 Mnemo。完整声明见项目根目录 THIRD_PARTY_NOTICES.md。
              </Dialog.Description>
              <div className="mt-5 flex justify-end">
                <Dialog.Close asChild>
                  <Button variant="primary">知道了</Button>
                </Dialog.Close>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </aside>
    </div>
  );
}
