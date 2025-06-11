import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';
import 'package:currency_converter_app/features/home/domain/repository/supported_repository.dart';
import 'package:dartz/dartz.dart';

abstract class GetSupportedCurrency {
  Future<Either<Exception, List<SupportedCurrency>>> call();
}

class GetSupportedCurrencyImpl {
  final SupportedRepository repository;

  GetSupportedCurrencyImpl(this.repository);

  Future<Either<Exception, List<SupportedCurrency>>> call() {
    return repository.getSupportedCurrency();
  }
}
