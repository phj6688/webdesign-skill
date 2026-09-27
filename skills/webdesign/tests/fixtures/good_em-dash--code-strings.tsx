import styled from "styled-components";

const Pull = styled.blockquote`
  font-style: italic;
  &::before { content: "— "; }
`;

const usage = `
import { Chart } from "@charts/core"; // Chart — the default export
`;

export function Quote() {
  return <Pull title={usage}>Measure twice, cut once.</Pull>;
}
