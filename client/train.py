"""
    init model unit test
"""
import os
import torch
import torch.utils.data
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import argparse
import socket
from datetime import datetime
from requests import get  # to make GET request

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4*4*50, 500)
        self.fc2 = nn.Linear(500, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4*4*50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

def download(url, file_name):
    with open(file_name, "wb") as file:
        response = get(url)
        file.write(response.content)

def train(model, train_loader, optimizer, epochs):
    model.train()
    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(train_loader):
            optimizer.zero_grad()
            output = model(data)
            loss = F.nll_loss(output, target)
            loss.backward()
            optimizer.step()

            pred = output.argmax(dim=1, keepdim=True)
            correct = pred.eq(target.view_as(pred)).sum().item()
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f} Acc: {:.2f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                       100. * batch_idx / len(train_loader),
                        loss.item(), correct/len(data) * 100))


    # TODO Save model in local file system with tagging
    model_tag = str(socket.gethostname()) + '-' + str(datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3])
    torch.save(model.state_dict(), os.path.join('./models', model_tag) + '.pt')
    # TODO send model to worker aggregator

def main(args):
    # Load Model
    if not os.path.exists(args.model):
        download(url=args.web_model, file_name=args.model)

    model = Net()
    optimizer = optim.SGD(model.parameters(),
                          lr=args.lr,
                          momentum=args.momentum)
    model.load_state_dict(torch.load(args.model))
    print(model)

    # Load Data
    flatten = lambda l: [item for sublist in l for item in sublist]
    if os.path.exists(args.data_path):
        load_data = torch.load(args.data_path)
        load_data = flatten(load_data)
        train_loader = torch.utils.data.DataLoader(load_data,
                                                   batch_size=64,
                                                   shuffle=True,)

        train(model, train_loader, optimizer, args.epoch)


if __name__ == '__main__':
    try:
        os.mkdir('./models')
    except:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--web_model', help='init_model',
                default='https://ywj-horovod.s3.ap-northeast-2.amazonaws.com/torchmodels/model.pt')
    parser.add_argument('--model', help='downloaded init model', default='/tmp/init_model.pt')
    parser.add_argument('--data_path', help='train data', default='/tmp/data.pt')
    parser.add_argument('--lr', help='learning rate', default=0.01, type=float)
    parser.add_argument('--momentum', help='momentum', default=0.5, type=float)
    parser.add_argument('--epoch', help='number of epoch', default=50, type=int)
    known_args, _ = parser.parse_known_args()
    print(known_args)
    main(args=known_args)