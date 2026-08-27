import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { translateText } from './translations';
import i18n from './config';

export type Locale = 'en' | 'zh-CN';

type LanguageContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (text: string) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);
const originalText = new WeakMap<Text, string>();
const originalAttributes = new WeakMap<Element, Map<string, string>>();

function translateElement(root: Node, locale: Locale) {
  const elements: Element[] = root instanceof Element ? [root] : [];
  if (root instanceof Element || root instanceof Document || root instanceof DocumentFragment) {
    elements.push(...Array.from(root.querySelectorAll('*')));
  }

  for (const element of elements) {
    for (const attribute of ['placeholder', 'title', 'aria-label']) {
      const current = element.getAttribute(attribute);
      if (current === null) continue;
      let originals = originalAttributes.get(element);
      if (!originals) {
        originals = new Map();
        originalAttributes.set(element, originals);
      }
      if (!originals.has(attribute)) originals.set(attribute, current);
      const source = originals.get(attribute) ?? current;
      const next = locale === 'zh-CN' ? translateText(source) : source;
      if (current !== next) element.setAttribute(attribute, next);
    }
  }

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = root instanceof Text ? [root] : [];
  while (walker.nextNode()) nodes.push(walker.currentNode as Text);
  for (const node of nodes) {
    const current = node.nodeValue ?? '';
    if (!current.trim()) continue;
    if (!originalText.has(node)) originalText.set(node, current);
    let source = originalText.get(node) ?? current;
    const previousTrimmed = source.trim();
    const previousTranslation = source.replace(previousTrimmed, translateText(previousTrimmed));
    if (current !== source && current !== previousTranslation) {
      originalText.set(node, current);
      source = current;
    }
    const trimmed = source.trim();
    const translated = locale === 'zh-CN' ? translateText(trimmed) : trimmed;
    const next = source.replace(trimmed, translated);
    if (current !== next) node.nodeValue = next;
  }
}

export const LanguageProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = localStorage.getItem('gitalerts-locale');
    if (saved === 'en' || saved === 'zh-CN') return saved;
    return navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en';
  });

  const setLocale = (next: Locale) => {
    localStorage.setItem('gitalerts-locale', next);
    setLocaleState(next);
  };

  useEffect(() => {
    document.documentElement.lang = locale;
    void i18n.changeLanguage(locale);
    const apply = () => translateElement(document.body, locale);
    apply();
    if (locale === 'en') return;
    const observer = new MutationObserver((mutations) => {
      observer.disconnect();
      for (const mutation of mutations) {
        if (mutation.type === 'characterData' && mutation.target.parentNode) {
          translateElement(mutation.target.parentNode, locale);
        }
        if (mutation.type === 'attributes') translateElement(mutation.target, locale);
        mutation.addedNodes.forEach((node) => translateElement(node, locale));
      }
      observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'title', 'aria-label'] });
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'title', 'aria-label'] });
    return () => observer.disconnect();
  }, [locale]);

  const value = useMemo(() => ({
    locale,
    setLocale,
    t: (text: string) => locale === 'zh-CN' ? i18n.t(text, { defaultValue: translateText(text) }) : text,
  }), [locale]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

// Context hooks intentionally live beside the provider to keep this small i18n layer cohesive.
// eslint-disable-next-line react-refresh/only-export-components
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within LanguageProvider');
  return context;
}
