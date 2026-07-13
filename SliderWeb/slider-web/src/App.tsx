import React, { useCallback, useEffect, useRef, useState } from 'react';
import PageComponent from './PageComponent';
import './App.css';


function App() {

  const [pages, setPages] = useState<any[]>([]);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(() => window.innerHeight);
  const [navHovered, setNavHovered] = useState(false);
  const appRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef({ y: 0, scrollTop: 0 });

  const maxScroll = Math.max((pages.length - 1) * viewportHeight, 0);
  const scrollHeight = pages.length * viewportHeight || viewportHeight;
  const thumbHeight = pages.length
    ? Math.max((viewportHeight / scrollHeight) * viewportHeight, 48)
    : viewportHeight;
  const thumbTop = maxScroll > 0
    ? (scrollTop / maxScroll) * (viewportHeight - thumbHeight)
    : 0;

  const scrollTo = useCallback((nextScroll: number) => {
    const appEl = appRef.current;
    if (!appEl) {
      return;
    }

    const clamped = Math.min(Math.max(nextScroll, 0), maxScroll);
    appEl.scrollTop = clamped;
    setScrollTop(clamped);
  }, [maxScroll]);

  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL}/pages.json`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to fetch pages: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setPages(data))
      .catch((error) => console.error('Error fetching pages:', error));
  }, []);

  useEffect(() => {
    const appEl = appRef.current;
    if (!appEl) {
      return;
    }

    const onScroll = () => setScrollTop(appEl.scrollTop);

    const onWheel = (e: WheelEvent) => {
      const maxScroll = appEl.scrollHeight - appEl.clientHeight;
      if (maxScroll <= 0) {
        return;
      }

      const nextScroll = appEl.scrollTop + e.deltaY;
      if (nextScroll < 0 || nextScroll > maxScroll) {
        return;
      }

      appEl.scrollTop = nextScroll;
      setScrollTop(nextScroll);
      e.preventDefault();
    };

    onScroll();
    appEl.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('wheel', onWheel, { passive: false });

    return () => {
      appEl.removeEventListener('scroll', onScroll);
      window.removeEventListener('wheel', onWheel);
    };
  }, [pages]);

  const onThumbMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    dragStartRef.current = { y: e.clientY, scrollTop };

    const onMouseMove = (moveEvent: MouseEvent) => {
      const trackHeight = viewportHeight - thumbHeight;
      if (trackHeight <= 0) {
        return;
      }

      const deltaY = moveEvent.clientY - dragStartRef.current.y;
      const scrollDelta = (deltaY / trackHeight) * maxScroll;
      scrollTo(dragStartRef.current.scrollTop + scrollDelta);
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).classList.contains('App-scrollbar-thumb')) {
      return;
    }

    const rect = e.currentTarget.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const trackHeight = viewportHeight - thumbHeight;
    const nextTop = Math.min(Math.max(clickY - thumbHeight / 2, 0), trackHeight);
    scrollTo((nextTop / trackHeight) * maxScroll);
  };

  useEffect(() => {
    const onResize = () => setViewportHeight(window.innerHeight);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const getTranslateX = useCallback((index: number) => {
    if (!viewportHeight) {
      return 0;
    }

    const sectionStart = index * viewportHeight;
    const progress = (scrollTop - sectionStart) / viewportHeight;
    const clamped = Math.min(Math.max(progress, 0), 1);
    return -clamped * 100;
  }, [scrollTop, viewportHeight]);

  const getHoleMarginLeft = useCallback((index: number) => {
    if (!viewportHeight || pages.length === 0) {
      return 0;
    }

    const maxMargin = index * -2;
    const activeIndex = Math.floor(scrollTop / viewportHeight);
    const progressInSection = (scrollTop % viewportHeight) / viewportHeight;
    const fullyInViewIndex = Math.min(
      pages.length - 1,
      progressInSection === 0 ? activeIndex : activeIndex + 1
    );

    if (index === fullyInViewIndex) {
      return 0;
    }

    if (index === activeIndex && progressInSection > 0) {
      return maxMargin * progressInSection;
    }

    return maxMargin;
  }, [scrollTop, viewportHeight, pages.length]);

  const getFullyInViewIndex = useCallback(() => {
    if (!viewportHeight || pages.length === 0) {
      return 0;
    }

    const activeIndex = Math.floor(scrollTop / viewportHeight);
    const progressInSection = (scrollTop % viewportHeight) / viewportHeight;
    return Math.min(
      pages.length - 1,
      progressInSection === 0 ? activeIndex : activeIndex + 1
    );
  }, [scrollTop, viewportHeight, pages.length]);

  const activePageId = pages[getFullyInViewIndex()]?.id;

  return (
    <>
      <div
        className="App"
        ref={appRef}
      >
        <div
          className="App-scroll-track"
          style={{ height: pages.length ? `${pages.length * 100}vh` : '100vh' }}
          aria-hidden="true"
        />
        <div className={`App-pages${navHovered ? ' App-pages--nav-hover' : ''}`}>
          {pages.map((page, index) => (
            <PageComponent
              key={page.id}
              page={page}
              index={index}
              pagesCount={pages.length}
              translateX={getTranslateX(index)}
              holeMarginLeft={getHoleMarginLeft(index)}
              navHovered={navHovered}
              isActivePage={page.id === activePageId}
              onNavEnter={() => setNavHovered(true)}
              onNavLeave={() => setNavHovered(false)}
            />
          ))}
        </div>
      </div>

       {
       //pages.length > 0 && (
        // <nav
        //   className={`page-nav-popup${navHovered ? ' page-nav-popup--visible' : ''}`}
        //   onMouseEnter={() => setNavHovered(true)}
        //   onMouseLeave={() => setNavHovered(false)}
        // >
        //   {pages.map((item, itemIndex) => (
        //     <a
        //       key={item.id}
        //       href={`#page-${item.id}`}
        //       className={item.id === activePageId ? 'page-nav-popup-item active' : 'page-nav-popup-item'}
        //       style={{
        //         backgroundColor: item.background,
        //         ['--item-min-width' as string]: `${(pages.length - itemIndex) * 15}vh`,
        //         transitionDelay: `${itemIndex * 0.06}s`,
        //       }}
        //     >
        //       {item.name}
        //     </a>
        //   ))}
        // </nav>
      //)
      }

      {pages.length > 1 && (
        <div className="App-scrollbar" aria-hidden="true">
          <div className="App-scrollbar-track" onClick={onTrackClick}>
            <div
              className="App-scrollbar-thumb"
              style={{ height: `${thumbHeight}px`, transform: `translateY(${thumbTop}px)` }}
              onMouseDown={onThumbMouseDown}
            />
          </div>
        </div>
      )}
    </>
  );
}

export default App;
