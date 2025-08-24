import { useMutation, useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import {
  type BodyLoginLoginAccessToken as AccessToken,
  Login,
  type Token,
  type UserPublic,
} from "@/client"
import { handleError } from "@/utils"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const response = await Login.loginWhoami()
      return response.data as unknown as UserPublic
    },
    enabled: isLoggedIn(),
  })

  const login = async (data: AccessToken) => {
    const response = await Login.loginLoginAccessToken({
      body: data,
    })
    const tokenData = response.data as unknown as Token
    localStorage.setItem("access_token", tokenData.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: any) => {
      handleError(err)
    },
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  return {
    loginMutation,
    logout,
    user,
    error,
    resetError: () => setError(null),
  }
}

export { isLoggedIn }
export default useAuth
