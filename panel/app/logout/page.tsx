"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-xl font-bold text-gray-600">در حال خروج از حساب...</div>
    </div>
  );
}