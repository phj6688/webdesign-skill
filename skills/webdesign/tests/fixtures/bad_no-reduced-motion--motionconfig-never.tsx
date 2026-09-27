import { MotionConfig, motion } from "motion/react";

export function Shell({ children }) {
  return (
    <MotionConfig reducedMotion="never">
      <motion.div animate={{ opacity: 1 }}>{children}</motion.div>
    </MotionConfig>
  );
}
