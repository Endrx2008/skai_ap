#include "mainwindow.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QScrollBar>
#include <QGuiApplication>
#include <QScreen>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent),
      output_text(nullptr),
      input_text(nullptr),
      sendButton(nullptr)
{
    output_text = new QTextEdit(this);
    input_text = new QLineEdit(this);
    sendButton = new QPushButton("Send", this);

    setWindowTitle("Skai");

    // Set background gradient for the main window
    QPalette pal = palette();
    QLinearGradient gradient(0, 0, 0, height());
    gradient.setColorAt(0, QColor("#2c3e50"));
    gradient.setColorAt(1, QColor("#4ca1af"));
    pal.setBrush(QPalette::Window, QBrush(gradient));
    setAutoFillBackground(true);
    setPalette(pal);

    output_text->setReadOnly(true);
    output_text->setStyleSheet(
        "background-color: #1e1e1e; "
        "color: #d4d4d4; "
        "font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; "
        "font-size: 14px; "
        "border-radius: 10px; "
        "padding: 10px;"
    );

    input_text->setPlaceholderText("Type your message here...");
    input_text->setStyleSheet(
        "background-color: #252526; "
        "color: #d4d4d4; "
        "font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; "
        "font-size: 14px; "
        "border-radius: 10px; "
        "padding: 8px;"
    );

    sendButton->setStyleSheet(
        "background-color: #0e639c; "
        "color: white; "
        "font-weight: bold; "
        "border-radius: 10px; "
        "padding: 8px 16px;"
        "min-width: 80px;"
    );

    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(15, 15, 15, 15);
    mainLayout->setSpacing(10);

    // Create a container widget for chat area
    QWidget *chatContainer = new QWidget(centralWidget);
    QGridLayout *chatLayout = new QGridLayout(chatContainer);
    chatLayout->setContentsMargins(0, 0, 0, 0);
    chatLayout->setSpacing(0);

    // Add output_text to chat layout
    chatLayout->addWidget(output_text, 0, 0);

    // Create clear button with bin icon
    clearButton = new QPushButton("Clear", chatContainer);
    // clearButton->setIcon(QIcon("bin.png"));
    clearButton->setFixedSize(60, 24);
    clearButton->setToolTip("Clear chat");
    clearButton->setStyleSheet("background: transparent; border: none; color: #a0a0a0; font-weight: bold;");

    // Add clear button to top right corner of chat layout
    chatLayout->addWidget(clearButton, 0, 0, Qt::AlignTop | Qt::AlignRight);

    // Add chat container to main layout
    mainLayout->addWidget(chatContainer);

    QHBoxLayout *inputLayout = new QHBoxLayout();
    inputLayout->setSpacing(10);
    inputLayout->addWidget(input_text);
    inputLayout->addWidget(sendButton);

    mainLayout->addLayout(inputLayout);

    connect(sendButton, &QPushButton::clicked, this, &MainWindow::onSendClicked);
    connect(input_text, &QLineEdit::returnPressed, this, &MainWindow::onSendClicked);

    // Set window size to approx 5 cm width (189 pixels) and height 400 pixels
    resize(189, 400);

    // Position window at the right side of the primary screen
    QScreen *screen = QGuiApplication::primaryScreen();
    if (screen) {
        QRect screenGeometry = screen->geometry();
        int x = screenGeometry.x() + screenGeometry.width() - width() - 10; // 10 px margin from right edge
        int y = screenGeometry.y() + 50; // 50 px from top
        move(x, y);
    }

    // Enable window transparency and remove window background
    setAttribute(Qt::WA_TranslucentBackground);
    setWindowFlags(windowFlags() | Qt::FramelessWindowHint);

    // Set initial output_text content to centered "say hello to skai" in light gray using QTextCursor
    output_text->clear();
    QTextCursor cursor(output_text->document());
    QTextBlockFormat blockFormat;
    blockFormat.setAlignment(Qt::AlignCenter);
    cursor.setBlockFormat(blockFormat);
    QTextCharFormat charFormat;
    charFormat.setForeground(QColor("#a0a0a0"));
    charFormat.setFontPointSize(13);
    charFormat.setFontFamily("'Segoe UI', Tahoma, Geneva, Verdana, sans-serif");
    cursor.insertText("say hello to skai", charFormat);
    cursor.insertBlock(); // Move to next block for future messages

    // Insert a new block with left alignment for subsequent messages
    QTextBlockFormat leftAlignFormat;
    leftAlignFormat.setAlignment(Qt::AlignLeft);
    cursor.setBlockFormat(leftAlignFormat);

    // Create clear button with bin icon
    connect(clearButton, &QPushButton::clicked, this, &MainWindow::clearChat);
    // The clear button is already created and added inside chatContainer layout, so remove this duplicate code
}


void MainWindow::clearChat()
{
    output_text->clear();
    firstMessageSent = false;

    QTextCursor cursor(output_text->document());
    QTextBlockFormat blockFormat;
    blockFormat.setAlignment(Qt::AlignCenter);
    cursor.setBlockFormat(blockFormat);

    QTextCharFormat charFormat;
    charFormat.setForeground(QColor("#a0a0a0"));
    charFormat.setFontPointSize(13);
    charFormat.setFontFamily("'Segoe UI', Tahoma, Geneva, Verdana, sans-serif");
    cursor.insertText("say hello to skai", charFormat);
    cursor.insertBlock();

    QTextBlockFormat leftAlignFormat;
    leftAlignFormat.setAlignment(Qt::AlignLeft);
    cursor.setBlockFormat(leftAlignFormat);
}

MainWindow::~MainWindow()
{
    // No dynamic resources to clean up
}

void MainWindow::appendMessage(const QString &sender, const QString &message)
{
    QString color = (sender == "You") ? "#569CD6" : "#CE9178";
    output_text->append(QString("<b><span style=\"color:%1;\">%2:</span></b> %3").arg(color, sender, message));
    QScrollBar *scrollBar = output_text->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void MainWindow::onSendClicked()
{
    QString userInput = input_text->text().trimmed();
    if (userInput.isEmpty())
        return;

    if (!firstMessageSent) {
        output_text->clear();
        firstMessageSent = true;
    }

    // Treat user input as input_text
    // Append user input to output_text as "input_text"
    appendMessage("You", userInput);

    // Simulate model response as "ciao"
    QString modelResponse = "hello";
    appendMessage("Model", modelResponse);

    input_text->clear();
}
