import { describe, it, expect, beforeEach } from "vitest";
import { getCookie } from "../cookies";

beforeEach(() => {
  Object.defineProperty(document, "cookie", {
    writable: true,
    value: "",
  });
});

describe("getCookie", () => {
  it("returns null when no cookies exist", () => {
    expect(getCookie("test")).toBeNull();
  });

  it("returns value for existing cookie", () => {
    document.cookie = "foo=bar; baz=qux";
    expect(getCookie("foo")).toBe("bar");
    expect(getCookie("baz")).toBe("qux");
  });

  it("returns null for non-existent cookie", () => {
    document.cookie = "foo=bar";
    expect(getCookie("missing")).toBeNull();
  });

  it("handles encoded cookie values", () => {
    document.cookie = "name=hello%20world";
    expect(getCookie("name")).toBe("hello world");
  });
});
