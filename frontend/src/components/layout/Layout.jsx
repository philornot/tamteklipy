import Header from "./Header";
import Footer from "./Footer";

function Layout({ children, user, onLogout }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header user={user} onLogout={onLogout} />

      <main className="flex-1">{children}</main>

      <Footer />
    </div>
  );
}

export default Layout;
