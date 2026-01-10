/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        balBlue: "#0076CE",
        balBlue100: "#E5F2FC",
        balRed: "#D62828",
        bgSoft: "#F5F6F7",
        bgSidebar: "#ECECEC",
        textDark: "#1F2937",
        textSoft: "#6B7280",
      },
      borderRadius: {
        card: "20px",
      },
      boxShadow: {
        card: "0 8px 22px rgba(0,0,0,0.06)",
        chatbtn: "0 20px 40px rgba(0,118,206,0.18)",
      },
    },
  },
  plugins: [],
};
