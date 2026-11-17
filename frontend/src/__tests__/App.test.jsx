import { beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import i18n from "../i18n";
import Login from "../pages/Login";

beforeAll(async () => {
  await i18n.changeLanguage("en");
});

describe("Login page", () => {
  it("renders the officer sign-in form", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );
    expect(screen.getByText("Officer Sign In")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. IO001")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^sign in$/i })).toBeInTheDocument();
  });

  it("shows the demo credentials hint", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );
    expect(screen.getByText("IO001")).toBeInTheDocument();
    expect(
      screen.getByText(/Password for all accounts: demo123/)
    ).toBeInTheDocument();
  });
});
