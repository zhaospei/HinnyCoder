
        String key = getInput("请输入KEY:");
        check(key);

        BigDecimal balance = getBalance(key);
        System.out.println("当前余额: " + balance);

        ChatGPT chatGPT = ChatGPT.builder()
                .apiKey(key)
                .proxy(proxy)
                .build()
                .init();

        while (true) {
            String input = getInput("请输入问题:");
            if (input.equals("exit")) {
                break;
            }
            String answer = chatGPT.chat(input);
            System.out.println("回答: " + answer);
        }
