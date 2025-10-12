import { Loader } from "lucide-react";

function Spinner({ size = 24, className = "", color = "primary" }) {
  const colorClasses = {
    primary: "text-primary-500",
    accent: "text-accent-500",
    white: "text-white",
    blue: "text-blue-500",
  };

  return (
    <Loader
      size={size}
      className={`animate-spin ${colorClasses[color] || colorClasses.primary} ${className}`}
    />
  );
}

export default Spinner;
