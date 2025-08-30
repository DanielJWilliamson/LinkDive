import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import type { NextAuthOptions } from "next-auth"

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    // Development/Testing provider for admin backdoor
    CredentialsProvider({
      id: "admin-backdoor",
      name: "Admin Backdoor",
      credentials: {
        email: { label: "Email", type: "email" }
      },
      async authorize(credentials) {
        // Allow admin backdoor for development/testing
        if (credentials?.email === 'admin') {
          return {
            id: 'admin-dev',
            email: 'admin',
            name: 'Admin User (Development)',
          }
        }
        return null
      }
    })
  ],
  callbacks: {
    async signIn({ user, account }) {
      // Allow admin backdoor
      if (user.email === 'admin' && account?.provider === 'admin-backdoor') {
        return true
      }
      // Restrict Google OAuth to @linkdive.ai domain  
      if (account?.provider === 'google' && user.email?.endsWith('@linkdive.ai')) {
        return true
      }
      return false
    },
    async session({ session }) {
      return session
    },
    async jwt({ token }) {
      return token
    }
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: "jwt",
  },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
