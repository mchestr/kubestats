import { Button } from "@chakra-ui/react"
import { FiRefreshCw } from "react-icons/fi"

interface SyncButtonProps {
  onSync: () => void
  size?: "sm" | "md" | "lg"
  variant?: "outline" | "solid" | "ghost"
  colorPalette?: string
  children?: React.ReactNode
  disabled?: boolean
}

export function SyncButton({
  onSync,
  size = "sm",
  variant = "outline",
  colorPalette,
  children = "Sync",
  disabled = false,
}: SyncButtonProps) {
  return (
    <Button
      size={size}
      variant={variant}
      colorPalette={colorPalette}
      onClick={onSync}
      disabled={disabled}
    >
      <FiRefreshCw />
      {children}
    </Button>
  )
}
