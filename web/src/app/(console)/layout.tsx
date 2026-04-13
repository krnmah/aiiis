import { ReactNode } from "react";

import { ConsoleShell } from "@/components/console-shell";

type Props = {
  children: ReactNode;
};

export default function ConsoleLayout({ children }: Props) {
  return <ConsoleShell>{children}</ConsoleShell>;
}
