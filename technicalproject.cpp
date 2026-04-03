/*
 * Game Zone — Windows GUI (Win32). Multiple mini-games in one window.
 *
 * Build (MinGW):
 *   g++ -std=c++17 -mwindows -o technicalproject.exe technicalproject.cpp
 *   (Uses WinMain so -municode is not required.)
 *
 * MSVC:
 *   cl /EHsc /std:c++17 /Fe:technicalproject.exe technicalproject.cpp user32.lib gdi32.lib
 */

#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cwchar>
#include <random>
#include <windows.h>

static int wfmt(wchar_t* buf, size_t cap, const wchar_t* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    const int r = _vsnwprintf(buf, cap, fmt, ap);
    va_end(ap);
    if (cap > 0)
        buf[cap - 1] = 0;
    return r;
}

static int wtoi(const wchar_t* s) {
    if (!s || !*s)
        return 0;
    return (int)wcstol(s, nullptr, 10);
}

namespace {

enum class Screen { Menu, Guess, RPS, TTT, Math };

struct AppState {
    Screen current = Screen::Menu;
    // Guess the number
    int guessSecret = 0;
    int guessTries = 0;
    static constexpr int kGuessMaxTries = 8;
    // Rock paper scissors
    int rpsYou = 0;
    int rpsCpu = 0;
    // Tic-tac-toe: ' ', 'X', 'O'
    char tttBoard[9]{};
    bool tttOver = false;
    // Quick math
    bool mathActive = false;
    int mathCorrect = 0;
    int mathTotal = 0;
    int mathSecondsLeft = 60;
    int mathExpected = 0;
};

HINSTANCE g_inst = nullptr;

// ---- Control IDs ----
enum : int {
    IDC_MENU_TITLE = 106,
    IDC_MENU_GUESS = 101,
    IDC_MENU_RPS = 102,
    IDC_MENU_TTT = 103,
    IDC_MENU_MATH = 104,
    IDC_MENU_EXIT = 105,

    IDC_GUESS_HELP = 201,
    IDC_GUESS_FEEDBACK = 202,
    IDC_GUESS_EDIT = 203,
    IDC_GUESS_BTN = 204,
    IDC_GUESS_RESTART = 205,
    IDC_GUESS_BACK = 206,

    IDC_RPS_SCORE = 301,
    IDC_RPS_RESULT = 302,
    IDC_RPS_ROCK = 303,
    IDC_RPS_PAPER = 304,
    IDC_RPS_SCISSORS = 305,
    IDC_RPS_RESTART = 306,
    IDC_RPS_BACK = 307,

    IDC_TTT_STATUS = 401,
    IDC_TTT_0 = 410,
    IDC_TTT_RESTART = 419,
    IDC_TTT_BACK = 420,

    IDC_MATH_PROBLEM = 501,
    IDC_MATH_TIMER = 502,
    IDC_MATH_SCORE = 503,
    IDC_MATH_EDIT = 504,
    IDC_MATH_SUBMIT = 505,
    IDC_MATH_RESTART = 506,
    IDC_MATH_BACK = 507,

    TIMER_MATH = 1,
};

int randomInt(int lo, int hi) {
    static thread_local std::mt19937 rng{std::random_device{}()};
    std::uniform_int_distribution<int> dist(lo, hi);
    return dist(rng);
}

AppState* stateOf(HWND w) {
    return reinterpret_cast<AppState*>(GetWindowLongPtrW(w, GWLP_USERDATA));
}

void setGroup(HWND parent, const int* ids, int n, int showCmd) {
    for (int i = 0; i < n; ++i) {
        HWND h = GetDlgItem(parent, ids[i]);
        if (h)
            ShowWindow(h, showCmd);
    }
}

void showScreen(HWND hwnd, AppState* st, Screen s) {
    static const int menuIds[] = {IDC_MENU_TITLE, IDC_MENU_GUESS, IDC_MENU_RPS,
                                    IDC_MENU_TTT, IDC_MENU_MATH, IDC_MENU_EXIT};
    static const int guessIds[] = {IDC_GUESS_HELP, IDC_GUESS_FEEDBACK, IDC_GUESS_EDIT,
                                   IDC_GUESS_BTN, IDC_GUESS_RESTART, IDC_GUESS_BACK};
    static const int rpsIds[] = {IDC_RPS_SCORE, IDC_RPS_RESULT, IDC_RPS_ROCK, IDC_RPS_PAPER,
                                   IDC_RPS_SCISSORS, IDC_RPS_RESTART, IDC_RPS_BACK};
    int tttIds[12] = {IDC_TTT_STATUS, IDC_TTT_RESTART, IDC_TTT_BACK};
    for (int k = 0; k < 9; ++k)
        tttIds[3 + k] = IDC_TTT_0 + k;
    static const int mathIds[] = {IDC_MATH_PROBLEM, IDC_MATH_TIMER, IDC_MATH_SCORE,
                                    IDC_MATH_EDIT, IDC_MATH_SUBMIT, IDC_MATH_RESTART,
                                    IDC_MATH_BACK};

    setGroup(hwnd, menuIds, (int)(sizeof menuIds / sizeof menuIds[0]), SW_HIDE);
    setGroup(hwnd, guessIds, (int)(sizeof guessIds / sizeof guessIds[0]), SW_HIDE);
    setGroup(hwnd, rpsIds, (int)(sizeof rpsIds / sizeof rpsIds[0]), SW_HIDE);
    setGroup(hwnd, tttIds, 12, SW_HIDE);
    setGroup(hwnd, mathIds, (int)(sizeof mathIds / sizeof mathIds[0]), SW_HIDE);

    st->current = s;

    if (s == Screen::Menu) {
        setGroup(hwnd, menuIds, (int)(sizeof menuIds / sizeof menuIds[0]), SW_SHOW);
        return;
    }
    if (s == Screen::Guess) {
        setGroup(hwnd, guessIds, (int)(sizeof guessIds / sizeof guessIds[0]), SW_SHOW);
        return;
    }
    if (s == Screen::RPS) {
        setGroup(hwnd, rpsIds, (int)(sizeof rpsIds / sizeof rpsIds[0]), SW_SHOW);
        return;
    }
    if (s == Screen::TTT) {
        setGroup(hwnd, tttIds, 12, SW_SHOW);
        return;
    }
    if (s == Screen::Math) {
        setGroup(hwnd, mathIds, (int)(sizeof mathIds / sizeof mathIds[0]), SW_SHOW);
    }
}

bool lineWinTTT(const char* b, char p) {
    const int lines[8][3] = {{0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {0, 3, 6}, {1, 4, 7},
                             {2, 5, 8}, {0, 4, 8}, {2, 4, 6}};
    for (auto& ln : lines) {
        if (b[ln[0]] == p && b[ln[1]] == p && b[ln[2]] == p)
            return true;
    }
    return false;
}

int cpuMoveTTT(char* board) {
    auto tryWin = [&](char p) -> int {
        for (int i = 0; i < 9; ++i) {
            if (board[i] != ' ')
                continue;
            board[i] = p;
            bool w = lineWinTTT(board, p);
            board[i] = ' ';
            if (w)
                return i;
        }
        return -1;
    };
    int w = tryWin('O');
    if (w >= 0)
        return w;
    int b = tryWin('X');
    if (b >= 0)
        return b;
    if (board[4] == ' ')
        return 4;
    const int order[] = {0, 2, 6, 8, 1, 3, 5, 7};
    for (int i : order) {
        if (board[i] == ' ')
            return i;
    }
    return -1;
}

void resetGuess(HWND hwnd, AppState* st) {
    st->guessSecret = randomInt(1, 100);
    st->guessTries = 0;
    SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_FEEDBACK),
                   L"I'm thinking of 1–100. You have 8 tries.");
    SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_EDIT), L"");
}

void resetRPS(HWND hwnd, AppState* st) {
    st->rpsYou = st->rpsCpu = 0;
    SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_SCORE), L"Score — You: 0   CPU: 0");
    SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_RESULT), L"First to 3 wins. Choose below.");
}

void resetTTT(HWND hwnd, AppState* st) {
    st->tttOver = false;
    for (int i = 0; i < 9; ++i) {
        st->tttBoard[i] = ' ';
        HWND cell = GetDlgItem(hwnd, IDC_TTT_0 + i);
        SetWindowTextW(cell, L" ");
        EnableWindow(cell, TRUE);
    }
    SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_STATUS), L"You are X. Click a square.");
}

void nextMathProblem(HWND hwnd, AppState* st) {
    if (!st->mathActive)
        return;
    const int a = randomInt(2, 12), b = randomInt(2, 12);
    const int op = randomInt(0, 1);
    wchar_t q[64];
    if (op == 0) {
        st->mathExpected = a + b;
        wfmt(q, 64, L"%d + %d = ?", a, b);
    } else {
        const int x = (std::max)(a, b), y = (std::min)(a, b);
        st->mathExpected = x - y;
        wfmt(q, 64, L"%d - %d = ?", x, y);
    }
    SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_PROBLEM), q);
    SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_EDIT), L"");
}

void startMath(HWND hwnd, AppState* st) {
    KillTimer(hwnd, TIMER_MATH);
    st->mathActive = true;
    st->mathCorrect = st->mathTotal = 0;
    st->mathSecondsLeft = 60;
    SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_SCORE), L"Correct: 0 / 0");
    wchar_t t[32];
    wfmt(t, 32, L"Time left: %d s", st->mathSecondsLeft);
    SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_TIMER), t);
    nextMathProblem(hwnd, st);
    SetTimer(hwnd, TIMER_MATH, 1000, nullptr);
}

void stopMath(HWND hwnd, AppState* st) {
    KillTimer(hwnd, TIMER_MATH);
    st->mathActive = false;
}

// ---- UI helpers ----
HWND makeStatic(HWND parent, int id, const wchar_t* text, int x, int y, int w, int cy) {
    HWND hwndCtl = CreateWindowExW(0, L"STATIC", text,
                                   WS_CHILD | SS_LEFT | SS_NOPREFIX, x, y, w, cy, parent,
                                   (HMENU)(INT_PTR)id, g_inst, nullptr);
    SendMessageW(hwndCtl, WM_SETFONT, (WPARAM)GetStockObject(DEFAULT_GUI_FONT), TRUE);
    return hwndCtl;
}

HWND makeButton(HWND parent, int id, const wchar_t* text, int x, int y, int w, int cy) {
    HWND hwndCtl = CreateWindowExW(0, L"BUTTON", text,
                                   WS_CHILD | BS_PUSHBUTTON, x, y, w, cy, parent,
                                   (HMENU)(INT_PTR)id, g_inst, nullptr);
    SendMessageW(hwndCtl, WM_SETFONT, (WPARAM)GetStockObject(DEFAULT_GUI_FONT), TRUE);
    return hwndCtl;
}

HWND makeEdit(HWND parent, int id, int x, int y, int w, int cy) {
    HWND hwndCtl = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
                                   WS_CHILD | ES_AUTOHSCROLL | ES_RIGHT, x, y, w, cy, parent,
                                   (HMENU)(INT_PTR)id, g_inst, nullptr);
    SendMessageW(hwndCtl, WM_SETFONT, (WPARAM)GetStockObject(DEFAULT_GUI_FONT), TRUE);
    return hwndCtl;
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    AppState* st = stateOf(hwnd);

    switch (msg) {
    case WM_CREATE: {
        st = new AppState();
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(st));
        const int mx = 120, my = 72, mw = 220, mh = 32, gap = 8;

        makeStatic(hwnd, IDC_MENU_TITLE, L"GAME ZONE — choose a game", mx, 24, 320, 28);
        makeButton(hwnd, IDC_MENU_GUESS, L"Guess the Number", mx, my, mw, mh);
        makeButton(hwnd, IDC_MENU_RPS, L"Rock · Paper · Scissors", mx, my + (mh + gap), mw, mh);
        makeButton(hwnd, IDC_MENU_TTT, L"Tic-Tac-Toe", mx, my + 2 * (mh + gap), mw, mh);
        makeButton(hwnd, IDC_MENU_MATH, L"Quick Math (60 sec)", mx, my + 3 * (mh + gap), mw, mh);
        makeButton(hwnd, IDC_MENU_EXIT, L"Exit", mx, my + 4 * (mh + gap), mw, mh);

        makeStatic(hwnd, IDC_GUESS_HELP, L"Enter a number from 1 to 100.", 24, 24, 360, 20);
        makeStatic(hwnd, IDC_GUESS_FEEDBACK, L"", 24, 48, 400, 40);
        makeEdit(hwnd, IDC_GUESS_EDIT, 24, 96, 120, 26);
        makeButton(hwnd, IDC_GUESS_BTN, L"Guess", 160, 94, 80, 30);
        makeButton(hwnd, IDC_GUESS_RESTART, L"New game", 260, 94, 90, 30);
        makeButton(hwnd, IDC_GUESS_BACK, L"← Main menu", 24, 300, 120, 30);

        makeStatic(hwnd, IDC_RPS_SCORE, L"Score — You: 0   CPU: 0", 24, 24, 360, 22);
        makeStatic(hwnd, IDC_RPS_RESULT, L"", 24, 52, 400, 44);
        makeButton(hwnd, IDC_RPS_ROCK, L"Rock", 24, 110, 90, 36);
        makeButton(hwnd, IDC_RPS_PAPER, L"Paper", 130, 110, 90, 36);
        makeButton(hwnd, IDC_RPS_SCISSORS, L"Scissors", 236, 110, 100, 36);
        makeButton(hwnd, IDC_RPS_RESTART, L"New match", 24, 170, 100, 30);
        makeButton(hwnd, IDC_RPS_BACK, L"← Main menu", 24, 300, 120, 30);

        makeStatic(hwnd, IDC_TTT_STATUS, L"", 24, 20, 400, 24);
        const int cs = 56, ox = 80, oy = 56;
        for (int r = 0; r < 3; ++r)
            for (int c = 0; c < 3; ++c) {
                const int i = r * 3 + c;
                makeButton(hwnd, IDC_TTT_0 + i, L" ", ox + c * (cs + 6), oy + r * (cs + 6),
                           cs, cs);
            }
        makeButton(hwnd, IDC_TTT_RESTART, L"New game", 24, 260, 100, 30);
        makeButton(hwnd, IDC_TTT_BACK, L"← Main menu", 260, 260, 120, 30);

        makeStatic(hwnd, IDC_MATH_PROBLEM, L"", 24, 24, 320, 28);
        makeStatic(hwnd, IDC_MATH_TIMER, L"Time left: 60 s", 24, 56, 200, 22);
        makeStatic(hwnd, IDC_MATH_SCORE, L"Correct: 0 / 0", 24, 82, 260, 22);
        makeEdit(hwnd, IDC_MATH_EDIT, 24, 116, 100, 26);
        makeButton(hwnd, IDC_MATH_SUBMIT, L"Submit", 140, 114, 80, 30);
        makeButton(hwnd, IDC_MATH_RESTART, L"Restart timer", 240, 114, 110, 30);
        makeButton(hwnd, IDC_MATH_BACK, L"← Main menu", 24, 300, 120, 30);

        showScreen(hwnd, st, Screen::Menu);
        return 0;
    }

    case WM_COMMAND: {
        if (!st)
            break;
        if (HIWORD(wParam) != BN_CLICKED)
            break;
        const int id = LOWORD(wParam);

        if (id == IDC_MENU_EXIT) {
            DestroyWindow(hwnd);
            return 0;
        }
        if (id == IDC_MENU_GUESS) {
            showScreen(hwnd, st, Screen::Guess);
            resetGuess(hwnd, st);
            return 0;
        }
        if (id == IDC_MENU_RPS) {
            showScreen(hwnd, st, Screen::RPS);
            resetRPS(hwnd, st);
            return 0;
        }
        if (id == IDC_MENU_TTT) {
            showScreen(hwnd, st, Screen::TTT);
            resetTTT(hwnd, st);
            return 0;
        }
        if (id == IDC_MENU_MATH) {
            showScreen(hwnd, st, Screen::Math);
            startMath(hwnd, st);
            return 0;
        }

        if (id == IDC_GUESS_BACK) {
            showScreen(hwnd, st, Screen::Menu);
            return 0;
        }
        if (id == IDC_GUESS_RESTART) {
            resetGuess(hwnd, st);
            return 0;
        }
        if (id == IDC_GUESS_BTN) {
            wchar_t buf[64]{};
            GetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_EDIT), buf, 63);
            if (!buf[0])
                return 0;
            int g = wtoi(buf);
            if (g < 1 || g > 100) {
                SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_FEEDBACK),
                               L"Enter a number between 1 and 100.");
                return 0;
            }
            st->guessTries++;
            wchar_t fb[160];
            if (g < st->guessSecret) {
                wfmt(fb, 160, L"Higher!  (%d / %d tries)", st->guessTries,
                     AppState::kGuessMaxTries);
            } else if (g > st->guessSecret) {
                wfmt(fb, 160, L"Lower!  (%d / %d tries)", st->guessTries,
                     AppState::kGuessMaxTries);
            } else {
                wfmt(fb, 160, L"You got it in %d tries!", st->guessTries);
                SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_FEEDBACK), fb);
                return 0;
            }
            SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_FEEDBACK), fb);
            if (st->guessTries >= AppState::kGuessMaxTries) {
                wfmt(fb, 160, L"Out of tries. The number was %d.", st->guessSecret);
                SetWindowTextW(GetDlgItem(hwnd, IDC_GUESS_FEEDBACK), fb);
            }
            return 0;
        }

        if (id == IDC_RPS_BACK) {
            showScreen(hwnd, st, Screen::Menu);
            return 0;
        }
        if (id == IDC_RPS_RESTART) {
            resetRPS(hwnd, st);
            return 0;
        }
        if (id == IDC_RPS_ROCK || id == IDC_RPS_PAPER || id == IDC_RPS_SCISSORS) {
            if (st->rpsYou >= 3 || st->rpsCpu >= 3)
                return 0;
            int y = (id == IDC_RPS_ROCK) ? 0 : (id == IDC_RPS_PAPER ? 1 : 2);
            const int k = randomInt(0, 2);
            const wchar_t* names[] = {L"Rock", L"Paper", L"Scissors"};
            wchar_t line[256];
            if (y == k) {
                wfmt(line, 256, L"You: %s   CPU: %s   - Draw", names[y], names[k]);
            } else if ((y + 1) % 3 == k) {
                st->rpsCpu++;
                wfmt(line, 256, L"You: %s   CPU: %s   - CPU wins round", names[y], names[k]);
            } else {
                st->rpsYou++;
                wfmt(line, 256, L"You: %s   CPU: %s   - You win round", names[y], names[k]);
            }
            SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_RESULT), line);
            wchar_t sc[128];
            wfmt(sc, 128, L"Score - You: %d   CPU: %d", st->rpsYou, st->rpsCpu);
            SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_SCORE), sc);
            if (st->rpsYou >= 3)
                SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_RESULT), L"*** You won the match! ***");
            else if (st->rpsCpu >= 3)
                SetWindowTextW(GetDlgItem(hwnd, IDC_RPS_RESULT), L"*** CPU won the match. ***");
            return 0;
        }

        if (id == IDC_TTT_BACK) {
            showScreen(hwnd, st, Screen::Menu);
            return 0;
        }
        if (id == IDC_TTT_RESTART) {
            resetTTT(hwnd, st);
            return 0;
        }
        if (id >= IDC_TTT_0 && id < IDC_TTT_0 + 9) {
            if (st->tttOver)
                return 0;
            const int idx = id - IDC_TTT_0;
            if (st->tttBoard[idx] != ' ')
                return 0;
            st->tttBoard[idx] = 'X';
            SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_0 + idx), L"X");
            EnableWindow(GetDlgItem(hwnd, IDC_TTT_0 + idx), FALSE);
            if (lineWinTTT(st->tttBoard, 'X')) {
                st->tttOver = true;
                SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_STATUS), L"You win!");
                return 0;
            }
            int filled = 0;
            for (int i = 0; i < 9; ++i) {
                if (st->tttBoard[i] != ' ')
                    filled++;
            }
            if (filled == 9) {
                SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_STATUS), L"Draw.");
                st->tttOver = true;
                return 0;
            }
            const int cm = cpuMoveTTT(st->tttBoard);
            if (cm >= 0) {
                st->tttBoard[cm] = 'O';
                SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_0 + cm), L"O");
                EnableWindow(GetDlgItem(hwnd, IDC_TTT_0 + cm), FALSE);
            }
            if (lineWinTTT(st->tttBoard, 'O')) {
                st->tttOver = true;
                SetWindowTextW(GetDlgItem(hwnd, IDC_TTT_STATUS), L"CPU wins.");
            }
            return 0;
        }

        if (id == IDC_MATH_BACK) {
            stopMath(hwnd, st);
            showScreen(hwnd, st, Screen::Menu);
            return 0;
        }
        if (id == IDC_MATH_RESTART) {
            startMath(hwnd, st);
            return 0;
        }
        if (id == IDC_MATH_SUBMIT) {
            if (!st->mathActive)
                return 0;
            wchar_t buf[64]{};
            GetWindowTextW(GetDlgItem(hwnd, IDC_MATH_EDIT), buf, 63);
            if (!buf[0])
                return 0;
            const int u = wtoi(buf);
            st->mathTotal++;
            if (u == st->mathExpected)
                st->mathCorrect++;
            wchar_t sc[64];
            wfmt(sc, 64, L"Correct: %d / %d", st->mathCorrect, st->mathTotal);
            SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_SCORE), sc);
            nextMathProblem(hwnd, st);
            return 0;
        }
        break;
    }

    case WM_TIMER: {
        if (!st)
            break;
        if (wParam != TIMER_MATH || !st->mathActive)
            break;
        st->mathSecondsLeft--;
        wchar_t t[48];
        wfmt(t, 48, L"Time left: %d s", st->mathSecondsLeft);
        SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_TIMER), t);
        if (st->mathSecondsLeft <= 0) {
            stopMath(hwnd, st);
            wchar_t done[160];
            wfmt(done, 160, L"Time's up!  Correct: %d / %d", st->mathCorrect, st->mathTotal);
            SetWindowTextW(GetDlgItem(hwnd, IDC_MATH_PROBLEM), done);
        }
        return 0;
    }

    case WM_DESTROY: {
        KillTimer(hwnd, TIMER_MATH);
        if (st) {
            SetWindowLongPtrW(hwnd, GWLP_USERDATA, 0);
            delete st;
        }
        PostQuitMessage(0);
        return 0;
    }
    default:
        break;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

} // namespace

int WINAPI WinMain(HINSTANCE hi, HINSTANCE, LPSTR, int show) {
    g_inst = hi;
    WNDCLASSW wc{};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hi;
    wc.lpszClassName = L"GameZoneWindow";
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassW(&wc);

    HWND hwnd = CreateWindowExW(0, L"GameZoneWindow", L"Game Zone",
                                WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
                                CW_USEDEFAULT, CW_USEDEFAULT, 480, 400, nullptr, nullptr, hi,
                                nullptr);
    ShowWindow(hwnd, show);
    UpdateWindow(hwnd);

    MSG msg{};
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}
