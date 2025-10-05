import { Loader } from "lucide-react";

function Spinner({ size = 24, className = "" }) {
  return (
    <Loader
      size={size}
      className={`animate-spin text-blue-500 ${className}`}
    />
  );
}

export default Spinner;